from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.safe_fs import (
    assert_no_link_like,
    is_link_like,
    iter_regular_files_no_links,
    secure_path_within,
)

_PHASE_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,63}$")
_EXCLUDED_PREFIXES = (
    "evidence/integrity/",
    "evidence/telemetry/",
    ".migrations/",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_relative_scope(relative: str) -> Path:
    value = Path(relative)
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise ValueError(f"scope d'intégrité hors projet: {relative}")
    return value


def _safe_scope_root(project: Path, relative: str) -> Path | None:
    value = _validate_relative_scope(relative)
    candidate = project / value
    if not candidate.exists() and not is_link_like(candidate):
        return None
    return secure_path_within(candidate, project, label="scope d'intégrité")


def _iter_scope_files(project: Path, roots: list[str]) -> list[Path]:
    project_root = project.resolve(strict=True)
    files: list[Path] = []
    for relative in roots:
        candidate = _safe_scope_root(project_root, relative)
        if candidate is None:
            continue
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                iter_regular_files_no_links(
                    candidate,
                    label=f"scope d'intégrité {relative}",
                )
            )
    unique: dict[str, Path] = {}
    for path in files:
        relative = path.relative_to(project_root).as_posix()
        if any(relative.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
            continue
        unique[relative] = path
    return [unique[key] for key in sorted(unique)]


def _records_for_scope(project: Path, roots: list[str]) -> list[dict[str, Any]]:
    project_root = project.resolve(strict=True)
    records: list[dict[str, Any]] = []
    for path in _iter_scope_files(project_root, roots):
        records.append(
            {
                "path": path.relative_to(project_root).as_posix(),
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    return records


def _aggregate_records(records: list[dict[str, Any]]) -> str:
    aggregate = hashlib.sha256()
    for record in sorted(records, key=lambda item: str(item["path"])):
        aggregate.update(
            f"{record['path']}\0{record['sha256']}\0{record['size']}\n".encode()
        )
    return aggregate.hexdigest()


def _integrity_root(project: Path) -> Path:
    project_root = project.resolve(strict=True)
    evidence = secure_path_within(
        project_root / "evidence",
        project_root,
        require_dir=True,
        label="preuves d'intégrité",
    )
    root = evidence / "integrity"
    if root.exists() or is_link_like(root):
        return secure_path_within(
            root,
            project_root,
            require_dir=True,
            label="preuves d'intégrité",
        )
    root.mkdir()
    return secure_path_within(
        root,
        project_root,
        require_dir=True,
        label="preuves d'intégrité",
    )


def snapshot_integrity(
    project: Path,
    phase: str,
    *,
    roots: list[str] | None = None,
) -> Path:
    normalized = phase.strip().upper()
    if not _PHASE_RE.fullmatch(normalized):
        raise ValueError(f"phase d'intégrité invalide: {phase}")
    scope = roots or [
        "project.json",
        "intake",
        "sources",
        "context",
        "work",
        "deliverables",
        "diagrams",
    ]
    if any(not isinstance(relative, str) for relative in scope):
        raise ValueError("scope d'intégrité: roots doit contenir uniquement des chaînes")
    records = _records_for_scope(project, scope)
    payload = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "phase": normalized,
        "roots": scope,
        "file_count": len(records),
        "aggregate_sha256": _aggregate_records(records),
        "files": records,
    }
    target = _integrity_root(project) / f"{_stamp()}-{normalized}.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def verify_integrity_snapshot(project: Path, snapshot: Path) -> list[str]:
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("snapshot d'intégrité invalide")
    roots = payload.get("roots", [])
    if not isinstance(roots, list) or any(not isinstance(item, str) for item in roots):
        raise ValueError("snapshot d'intégrité: roots invalide")
    records = payload.get("files", [])
    if not isinstance(records, list):
        raise ValueError("snapshot d'intégrité: files invalide")

    failures: list[str] = []
    expected: dict[str, dict[str, Any]] = {}
    canonical_records: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            failures.append("record invalide")
            continue
        relative = str(record.get("path", ""))
        try:
            normalized = _validate_relative_scope(relative).as_posix()
        except ValueError:
            failures.append(f"chemin non sûr: {relative}")
            continue
        if normalized in expected:
            failures.append(f"record dupliqué: {normalized}")
            continue
        expected_hash = str(record.get("sha256", ""))
        try:
            expected_size = int(record["size"])
        except (KeyError, TypeError, ValueError):
            failures.append(f"taille invalide: {normalized}")
            continue
        normalized_record = {
            "path": normalized,
            "sha256": expected_hash,
            "size": expected_size,
        }
        expected[normalized] = normalized_record
        canonical_records.append(normalized_record)

    declared_aggregate = str(payload.get("aggregate_sha256", ""))
    if declared_aggregate != _aggregate_records(canonical_records):
        failures.append("snapshot: digest agrégé incohérent")

    observed_records = _records_for_scope(project, roots)
    observed = {str(record["path"]): record for record in observed_records}
    for relative in sorted(set(expected) | set(observed)):
        expected_record = expected.get(relative)
        observed_record = observed.get(relative)
        if expected_record is None:
            failures.append(f"ajouté: {relative}")
            continue
        if observed_record is None:
            failures.append(f"absent: {relative}")
            continue
        if (
            observed_record["sha256"] != expected_record["sha256"]
            or observed_record["size"] != expected_record["size"]
        ):
            failures.append(f"modifié: {relative}")
    return failures


def latest_integrity_snapshot(project: Path, phase: str | None = None) -> Path | None:
    project_root = project.resolve(strict=True)
    evidence = project_root / "evidence"
    if not evidence.exists() or is_link_like(evidence):
        if is_link_like(evidence):
            raise ValueError(f"snapshots d'intégrité: lien/reparse point interdit: {evidence}")
        return None
    secure_path_within(
        evidence,
        project_root,
        require_dir=True,
        label="snapshots d'intégrité",
    )
    root = evidence / "integrity"
    if not root.exists() and not is_link_like(root):
        return None
    safe_root = secure_path_within(
        root,
        project_root,
        require_dir=True,
        label="snapshots d'intégrité",
    )
    assert_no_link_like(safe_root, label="snapshots d'intégrité")
    suffix = f"-{phase.strip().upper()}.json" if phase else ".json"
    candidates = sorted(
        path for path in safe_root.glob("*.json") if path.name.endswith(suffix)
    )
    return candidates[-1] if candidates else None
