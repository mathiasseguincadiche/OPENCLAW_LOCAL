from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract

_LOCAL_REQUIRED = {
    "local_tests_green",
    "documentation_validated",
    "secret_scan_clean",
    "dependency_scan_reviewed",
    "git_status_reviewed",
    "ignore_rules_reviewed",
    "local_paths_removed",
    "rollback_documented",
    "independent_local_audit",
}
_FINAL_REQUIRED = {
    "canonical_repository_url",
    "published_commit_sha",
    "remote_ci_green",
    "clean_clone_validated",
    "independent_remote_audit",
    "merge_approved",
    "release_or_documented_no_release_decision",
    "human_final_approval",
}
_HUMAN_TARGETS = {"REMOTE_CREATED", "RELEASE_CREATED", "PUBLISHED_AND_VERIFIED"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _path(project: Path) -> Path:
    policy = load_contract("publication_policy.yaml")
    return project / str(policy.get("artifact", "context/publication.json"))


def _read(project: Path) -> dict[str, Any]:
    path = _path(project)
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("publication.json invalide")
    return data


def _write(project: Path, payload: dict[str, Any]) -> Path:
    path = _path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def initialize_publication(project: Path) -> Path:
    payload = {
        "schema_version": "1.0.0",
        "state": "LOCAL_IN_PROGRESS",
        "forge": None,
        "visibility": "private",
        "evidence": {},
        "history": [],
        "updated_at": _now(),
    }
    return _write(project, payload)


def record_publication_evidence(
    project: Path,
    key: str,
    value: bool | str,
    *,
    actor: str = "human",
) -> dict[str, Any]:
    payload = _read(project)
    evidence = payload.setdefault("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("publication.evidence invalide")
    evidence[key] = value
    payload.setdefault("history", []).append(
        {
            "at": _now(),
            "event": "evidence",
            "key": key,
            "value": value,
            "actor": actor,
        }
    )
    payload["updated_at"] = _now()
    _write(project, payload)
    return payload


def _require_true(evidence: dict[str, Any], keys: set[str]) -> None:
    missing = sorted(key for key in keys if evidence.get(key) is not True)
    if missing:
        raise ValueError("preuves publication manquantes: " + ", ".join(missing))


def _assert_transition_gates(
    target: str,
    evidence: dict[str, Any],
    *,
    human_approved: bool,
) -> None:
    if target == "LOCAL_VALIDATED":
        _require_true(evidence, _LOCAL_REQUIRED)
    if target == "READY_TO_PUBLISH" and evidence.get("local_package_reviewed") is not True:
        raise ValueError("local_package_reviewed requis avant READY_TO_PUBLISH")
    if target in _HUMAN_TARGETS and not human_approved:
        raise PermissionError(f"approbation humaine requise avant {target}")
    if target == "CI_GREEN" and evidence.get("remote_ci_green") is not True:
        raise ValueError("remote_ci_green requis avant CI_GREEN")
    if target == "REMOTE_CLONE_VALIDATED" and evidence.get("clean_clone_validated") is not True:
        raise ValueError("clean_clone_validated requis avant REMOTE_CLONE_VALIDATED")
    if target == "RELEASE_CREATED" and evidence.get("release_created") is not True:
        raise ValueError("release_created requis avant RELEASE_CREATED")
    if target == "PUBLISHED_AND_VERIFIED":
        missing = sorted(key for key in _FINAL_REQUIRED if not evidence.get(key))
        if missing:
            raise ValueError("preuves finales publication manquantes: " + ", ".join(missing))


def transition_publication(
    project: Path,
    target: str,
    *,
    actor: str,
    human_approved: bool = False,
) -> dict[str, Any]:
    policy = load_contract("publication_policy.yaml")
    payload = _read(project)
    current = str(payload.get("state", ""))
    allowed = policy.get("transitions", {}).get(current, [])
    if target not in allowed:
        raise ValueError(f"transition publication interdite: {current} -> {target}")

    evidence = payload.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("publication.evidence invalide")
    _assert_transition_gates(target, evidence, human_approved=human_approved)

    if target == "REMOTE_CREATED":
        forge = evidence.get("forge")
        if forge not in set(policy.get("supported_forges", [])):
            raise ValueError("forge github ou gitlab requise avant REMOTE_CREATED")
        payload["forge"] = forge
        payload["visibility"] = evidence.get(
            "visibility",
            policy.get("default_visibility", "private"),
        )

    payload["state"] = target
    payload.setdefault("history", []).append(
        {
            "at": _now(),
            "from": current,
            "to": target,
            "actor": actor,
        }
    )
    payload["updated_at"] = _now()
    _write(project, payload)
    return payload
