from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _policy() -> dict[str, Any]:
    return load_contract("publication_policy.yaml")


def publication_path(project: Path) -> Path:
    relative = _policy().get("artifact", "context/publication/publication.json")
    return project / str(relative)


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_publication(project: Path) -> dict[str, Any]:
    path = publication_path(project)
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("publication.json invalide")
    return payload


def initialize_publication(project: Path) -> Path:
    policy = _policy()
    payload = {
        "schema_version": "1.0.0",
        "state": "LOCAL_IN_PROGRESS",
        "visibility": policy.get("default_visibility", "private"),
        "canonical_forge": None,
        "canonical_repository_url": None,
        "published_commit_sha": None,
        "release_created": False,
        "release_or_documented_no_release_decision": False,
        "checks": {
            item: False for item in policy.get("prepublication_checks", [])
        },
        "remote_evidence": {
            "remote_ci_green": False,
            "clean_clone_validated": False,
            "independent_remote_audit": False,
        },
        "approvals": {"human_final_approval": False},
        "history": [],
        "updated_at": _now(),
    }
    path = publication_path(project)
    _write(path, payload)
    return path


def set_publication_evidence(
    project: Path,
    *,
    key: str,
    value: bool | str,
) -> dict[str, Any]:
    payload = load_publication(project)
    if key in payload.get("checks", {}):
        payload["checks"][key] = bool(value)
    elif key in payload.get("remote_evidence", {}):
        payload["remote_evidence"][key] = bool(value)
    elif key == "canonical_repository_url":
        payload[key] = str(value).strip() or None
    elif key == "published_commit_sha":
        payload[key] = str(value).strip() or None
    elif key == "canonical_forge":
        forge = str(value).strip().lower()
        if forge not in set(_policy().get("supported_forges", [])):
            raise ValueError(f"forge non supportée: {forge}")
        payload[key] = forge
    elif key in {
        "release_created",
        "release_or_documented_no_release_decision",
        "human_final_approval",
    }:
        if key == "human_final_approval":
            payload.setdefault("approvals", {})[key] = bool(value)
        else:
            payload[key] = bool(value)
    else:
        raise KeyError(f"preuve publication inconnue: {key}")
    payload["updated_at"] = _now()
    _write(publication_path(project), payload)
    return payload


def _assert_transition_gates(
    payload: dict[str, Any],
    target: str,
    *,
    human_approved: bool,
) -> None:
    policy = _policy()
    if target == "LOCAL_VALIDATED":
        required = set(policy.get("prepublication_checks", []))
        checks = payload.get("checks", {})
        missing = sorted(item for item in required if checks.get(item) is not True)
        if missing:
            raise ValueError(
                "checks locaux incomplets: " + ", ".join(missing)
            )
    if target == "READY_TO_PUBLISH" and payload.get("state") != "LOCAL_VALIDATED":
        raise ValueError("LOCAL_VALIDATED requis avant publication")
    if target in set(policy.get("human_approval_required", [])) and not human_approved:
        raise PermissionError(f"approbation humaine requise avant {target}")
    if target == "REMOTE_CREATED":
        if not payload.get("canonical_forge"):
            raise ValueError("canonical_forge requis")
        if not payload.get("canonical_repository_url"):
            raise ValueError("canonical_repository_url requis")
    if target == "CI_GREEN":
        if payload.get("remote_evidence", {}).get("remote_ci_green") is not True:
            raise ValueError("preuve remote_ci_green requise")
    if target == "REMOTE_CLONE_VALIDATED":
        if payload.get("remote_evidence", {}).get("clean_clone_validated") is not True:
            raise ValueError("preuve clean_clone_validated requise")
    if target == "RELEASE_CREATED" and payload.get("release_created") is not True:
        raise ValueError("preuve release_created requise")
    if target == "PUBLISHED_AND_VERIFIED":
        required = policy.get("published_and_verified_requires", [])
        values = {
            "canonical_repository_url": bool(payload.get("canonical_repository_url")),
            "published_commit_sha": bool(payload.get("published_commit_sha")),
            "remote_ci_green": payload.get("remote_evidence", {}).get("remote_ci_green"),
            "clean_clone_validated": payload.get("remote_evidence", {}).get(
                "clean_clone_validated"
            ),
            "independent_remote_audit": payload.get("remote_evidence", {}).get(
                "independent_remote_audit"
            ),
            "release_or_documented_no_release_decision": payload.get(
                "release_or_documented_no_release_decision"
            ),
            "human_final_approval": payload.get("approvals", {}).get(
                "human_final_approval"
            ),
        }
        missing = sorted(item for item in required if values.get(item) is not True)
        if missing:
            raise ValueError(
                "preuves de publication finale incomplètes: " + ", ".join(missing)
            )


def transition_publication(
    project: Path,
    target: str,
    *,
    actor: str,
    reason: str,
    human_approved: bool = False,
) -> dict[str, Any]:
    payload = load_publication(project)
    policy = _policy()
    current = str(payload.get("state", ""))
    states = set(policy.get("states", []))
    if target not in states:
        raise ValueError(f"état publication inconnu: {target}")
    allowed = policy.get("transitions", {}).get(current, [])
    if target not in allowed:
        raise ValueError(f"transition publication interdite: {current} -> {target}")
    _assert_transition_gates(payload, target, human_approved=human_approved)
    now = _now()
    payload.setdefault("history", []).append(
        {
            "at": now,
            "from": current,
            "to": target,
            "actor": actor,
            "reason": reason,
        }
    )
    payload["state"] = target
    payload["updated_at"] = now
    _write(publication_path(project), payload)
    return payload
