from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.safe_fs import assert_no_link_like, iter_regular_files_no_links

_GUARD_FILE = ".openclaw-local-input-guard.json"
_DEFAULT_PROTECTED = ("intake", "sources", "context/exchange")
_DEFAULT_OUTPUTS = ("work", "deliverables", "evidence", "diagrams")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_guard(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise PermissionError(f"{label} absent: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PermissionError(f"{label} invalide: {path}")
    return payload


def _protected_inputs(agent_id: str) -> tuple[str, ...]:
    policy = load_contract("tool_policy.yaml")
    enforcement = policy.get("write_enforcement", {})
    defaults = enforcement.get("protected_inputs", list(_DEFAULT_PROTECTED))
    entry = policy.get("agents", {}).get(agent_id, {})
    values = entry.get("protected_inputs", defaults)
    if not isinstance(values, list) or any(
        not isinstance(item, str) for item in values
    ):
        raise ValueError(f"tool_policy: protected_inputs invalide pour {agent_id}")
    return tuple(values)


def allowed_output_kinds(agent_id: str) -> tuple[str, ...]:
    policy = load_contract("tool_policy.yaml")
    entry = policy.get("agents", {}).get(agent_id)
    if not isinstance(entry, dict):
        raise ValueError(f"tool_policy: agent inconnu: {agent_id}")
    values = entry.get("collect_scopes", list(_DEFAULT_OUTPUTS))
    if not isinstance(values, list) or any(
        not isinstance(item, str) for item in values
    ):
        raise ValueError(f"tool_policy: collect_scopes invalide pour {agent_id}")
    unknown = sorted(set(values) - set(_DEFAULT_OUTPUTS))
    if unknown:
        raise ValueError(
            f"tool_policy: collect_scopes inconnus pour {agent_id}: "
            + ", ".join(unknown)
        )
    return tuple(values)


def _snapshot(workspace_project: Path, agent_id: str) -> dict[str, Any]:
    entries: dict[str, str] = {}
    for relative in _protected_inputs(agent_id):
        root = workspace_project / relative
        if not root.exists():
            continue
        assert_no_link_like(root, label=f"workspace guard {relative}")
        if root.is_file():
            entries[relative] = _sha256(root)
            continue
        for path in iter_regular_files_no_links(
            root,
            label=f"workspace guard {relative}",
        ):
            key = path.relative_to(workspace_project).as_posix()
            entries[key] = _sha256(path)
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.1.0",
        "generated_at": _now(),
        "agent_id": agent_id,
        "protected_inputs": list(_protected_inputs(agent_id)),
        "entries": entries,
        "aggregate_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def write_workspace_guard(
    workspace_project: Path,
    agent_id: str,
    *,
    reference_path: Path | None = None,
) -> Path:
    payload = _snapshot(workspace_project, agent_id)
    target = workspace_project / _GUARD_FILE
    _write_json(target, payload)
    if reference_path is not None:
        _write_json(reference_path, payload)
    return target


def validate_workspace_guard(
    workspace_project: Path,
    agent_id: str,
    *,
    reference_path: Path | None = None,
) -> None:
    local_path = workspace_project / _GUARD_FILE
    local = _load_guard(local_path, label=f"workspace guard local pour {agent_id}")
    expected = local
    if reference_path is not None:
        expected = _load_guard(
            reference_path,
            label=f"workspace guard plateforme pour {agent_id}",
        )
        if local.get("aggregate_sha256") != expected.get("aggregate_sha256"):
            raise PermissionError(
                f"workspace guard local altéré ou régénéré par {agent_id}"
            )
        if local.get("agent_id") != expected.get("agent_id"):
            raise PermissionError(f"workspace guard local incohérent pour {agent_id}")

    observed = _snapshot(workspace_project, agent_id)
    if expected.get("agent_id") != agent_id:
        raise PermissionError(f"workspace guard attribué au mauvais agent: {agent_id}")
    if expected.get("aggregate_sha256") != observed.get("aggregate_sha256"):
        raw_entries = expected.get("entries", {})
        expected_entries = raw_entries if isinstance(raw_entries, dict) else {}
        observed_entries = observed.get("entries", {})
        changed = sorted(
            key
            for key in set(expected_entries) | set(observed_entries)
            if expected_entries.get(key) != observed_entries.get(key)
        )
        preview = ", ".join(changed[:8]) or "contenu protégé"
        raise PermissionError(
            f"workspace guard: entrée protégée modifiée par {agent_id}: {preview}"
        )
