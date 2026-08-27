from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


def _iter_scope_files(project: Path, roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for relative in roots:
        candidate = project / relative
        if candidate.is_symlink():
            continue
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                path
                for path in candidate.rglob("*")
                if path.is_file() and not path.is_symlink()
            )
    unique: dict[str, Path] = {}
    for path in files:
        relative = path.relative_to(project).as_posix()
        if any(relative.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
            continue
        unique[relative] = path
    return [unique[key] for key in sorted(unique)]


def snapshot_integrity(
    project: Path,
    phase: str,
    *,
    roots: list[str] | None = None,
) -> Path:
    normalized = phase.strip().upper()
    if not _PHASE_RE.fullmatch(normalized):
        raise ValueError(f"phase d'intégrité invalide: {phase}")
    scope = roots or ["project.json", "intake", "sources", "context", "work", "deliverables", "diagrams"]
    records: list[dict[str, Any]] = []
    aggregate = hashlib.sha256()
    for path in _iter_scope_files(project, scope):
        relative = path.relative_to(project).as_posix()
        digest = _sha256(path)
        size = path.stat().st_size
        records.append({"path": relative, "sha256": digest, "size": size})
        aggregate.update(f"{relative}\0{digest}\0{size}\n".encode())
    payload = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "phase": normalized,
        "roots": scope,
        "file_count": len(records),
        "aggregate_sha256": aggregate.hexdigest(),
        "files": records,
    }
    target = project / "evidence" / "integrity" / f"{_stamp()}-{normalized}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def verify_integrity_snapshot(project: Path, snapshot: Path) -> list[str]:
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("snapshot d'intégrité invalide")
    records = payload.get("files", [])
    if not isinstance(records, list):
        raise ValueError("snapshot d'intégrité: files invalide")
    failures: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            failures.append("record invalide")
            continue
        relative = str(record.get("path", ""))
        expected = str(record.get("sha256", ""))
        path = project / relative
        if not path.is_file():
            failures.append(f"absent: {relative}")
            continue
        observed = _sha256(path)
        if observed != expected:
            failures.append(f"modifié: {relative}")
    return failures


def latest_integrity_snapshot(project: Path, phase: str | None = None) -> Path | None:
    root = project / "evidence" / "integrity"
    if not root.is_dir():
        return None
    suffix = f"-{phase.strip().upper()}.json" if phase else ".json"
    candidates = sorted(path for path in root.glob("*.json") if path.name.endswith(suffix))
    return candidates[-1] if candidates else None
