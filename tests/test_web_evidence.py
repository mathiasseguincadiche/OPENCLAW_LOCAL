from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from clawlocal.config import load_contract
from clawlocal.project_web_evidence import (
    project_web_evidence_failures,
    task_web_evidence_failures,
)
from clawlocal.web_evidence import validate_web_evidence_payload


def _now() -> datetime:
    return datetime(2026, 8, 28, 18, 0, tzinfo=UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _payload() -> dict[str, object]:
    now = _now()
    return {
        "schema_version": "1.0.0",
        "generated_at": _iso(now),
        "task_id": "research-current-runtime",
        "sources": [
            {
                "source_id": "official",
                "url": "https://example.com/releases/latest",
                "title": "Latest release",
                "publisher": "Example Project",
                "authority": "source_of_truth",
                "published_at": None,
                "updated_at": None,
                "retrieved_at": _iso(now - timedelta(minutes=10)),
                "date_status": "not_exposed",
                "supports_currentness": True,
            },
            {
                "source_id": "secondary",
                "url": "https://example.net/release-analysis",
                "title": "Release analysis",
                "publisher": "Independent Publisher",
                "authority": "secondary",
                "published_at": _iso(now - timedelta(hours=3)),
                "updated_at": None,
                "retrieved_at": _iso(now - timedelta(minutes=5)),
                "date_status": "known",
                "supports_currentness": False,
            },
        ],
        "runtime_evidence": [
            {
                "evidence_id": "runtime-schema",
                "kind": "schema",
                "observed_at": _iso(now - timedelta(minutes=2)),
                "result": "PASS",
                "command": "openclaw config schema",
                "exit_code": 0,
                "artifact": "runtime/generated/openclaw.schema.json",
            }
        ],
        "claims": [
            {
                "claim_id": "claim-provider",
                "text": "La configuration est supportée par le runtime installé.",
                "volatility": "current",
                "criticality": "high",
                "status": "VERIFIED",
                "confidence": "HIGH",
                "source_ids": ["official", "secondary"],
                "runtime_evidence_ids": ["runtime-schema"],
                "machine_verifiable": True,
                "currentness_basis": "live_runtime",
            }
        ],
        "conflicts": [],
    }


def test_web_policy_contract_is_fail_closed() -> None:
    policy = load_contract("web_policy.yaml")
    verification = policy["source_verification"]
    enforcement = policy["project_enforcement"]
    freshness = policy["freshness_policy"]

    assert policy["schema_version"] == "2.0.0"
    assert freshness["current_fact_requires_web"] is True
    assert freshness["retrieval_max_age_hours"] == 24
    assert verification["source_count_target"] == 2
    assert verification["distinct_publishers_for_corroboration"] is True
    assert verification["unresolved_conflict_blocks_acceptance"] is True
    assert verification["machine_verifiable_claim_requires_runtime_evidence"] is True
    assert enforcement["web_required_evidence_marker"] == "web_evidence"
    assert enforcement["runtime_required_evidence_marker"] == "runtime_evidence"
    assert enforcement["require_before_task_pass"] is True


def test_valid_current_machine_verifiable_claim_passes() -> None:
    validate_web_evidence_payload(_payload(), now=_now(), require_runtime=True)


def test_stale_currentness_source_is_rejected() -> None:
    payload = _payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    official = sources[0]
    assert isinstance(official, dict)
    official["retrieved_at"] = _iso(_now() - timedelta(hours=25))

    with pytest.raises(ValueError, match="currentness"):
        validate_web_evidence_payload(payload, now=_now())


def test_machine_verifiable_claim_without_runtime_is_rejected() -> None:
    payload = _payload()
    payload["runtime_evidence"] = []
    claims = payload["claims"]
    assert isinstance(claims, list)
    claim = claims[0]
    assert isinstance(claim, dict)
    claim["runtime_evidence_ids"] = []

    with pytest.raises(ValueError, match="preuve runtime obligatoire"):
        validate_web_evidence_payload(payload, now=_now())


def test_open_source_conflict_is_rejected() -> None:
    payload = _payload()
    payload["conflicts"] = [
        {
            "conflict_id": "conflict-001",
            "claim_ids": ["claim-provider"],
            "description": "Deux sources donnent des versions incompatibles.",
            "status": "OPEN",
        }
    ]

    with pytest.raises(ValueError, match="contradiction non résolue"):
        validate_web_evidence_payload(payload, now=_now())


def test_two_publishers_required_without_source_of_truth() -> None:
    payload = _payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    official = sources[0]
    assert isinstance(official, dict)
    official["authority"] = "primary"
    sources.pop()
    claims = payload["claims"]
    assert isinstance(claims, list)
    claim = claims[0]
    assert isinstance(claim, dict)
    claim["source_ids"] = ["official"]

    with pytest.raises(ValueError, match="2 sources requises"):
        validate_web_evidence_payload(payload, now=_now())


def test_source_of_truth_may_stand_alone_for_non_runtime_claim() -> None:
    payload = _payload()
    payload["sources"] = [deepcopy(payload["sources"][0])]  # type: ignore[index]
    payload["runtime_evidence"] = []
    claims = payload["claims"]
    assert isinstance(claims, list)
    claim = claims[0]
    assert isinstance(claim, dict)
    claim["source_ids"] = ["official"]
    claim["runtime_evidence_ids"] = []
    claim["machine_verifiable"] = False
    claim["currentness_basis"] = "official_latest_release"

    validate_web_evidence_payload(payload, now=_now())


def _write_project_plan(project: Path, required_evidence: list[str]) -> None:
    path = project / "context" / "project_plan.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tasks": [
                    {
                        "id": "research-current-runtime",
                        "required_evidence": required_evidence,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_project_gate_blocks_missing_required_web_evidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _write_project_plan(project, ["web_evidence", "runtime_evidence"])

    failures = task_web_evidence_failures(project, "research-current-runtime")
    assert failures
    assert "web_evidence.json" in failures[0]


def test_project_gate_accepts_valid_required_web_evidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _write_project_plan(project, ["web_evidence", "runtime_evidence"])
    path = project / "evidence" / "research-current-runtime" / "web_evidence.json"
    path.parent.mkdir(parents=True)
    dynamic_payload = _payload()
    dynamic_now = datetime.now(UTC)
    dynamic_payload["generated_at"] = _iso(dynamic_now)
    sources = dynamic_payload["sources"]
    assert isinstance(sources, list)
    for source in sources:
        assert isinstance(source, dict)
        source["retrieved_at"] = _iso(dynamic_now - timedelta(minutes=1))
    runtime_items = dynamic_payload["runtime_evidence"]
    assert isinstance(runtime_items, list)
    runtime = runtime_items[0]
    assert isinstance(runtime, dict)
    runtime["observed_at"] = _iso(dynamic_now - timedelta(minutes=1))
    path.write_text(json.dumps(dynamic_payload), encoding="utf-8")

    assert task_web_evidence_failures(project, "research-current-runtime") == []
    assert project_web_evidence_failures(project) == []
