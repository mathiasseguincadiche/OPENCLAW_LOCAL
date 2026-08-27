from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.project_contracts import (
    PROJECT_SCHEMA_VERSION,
    build_project_manifest,
    validate_project_manifest,
)
from clawlocal.project_governance import initialize_governance
from clawlocal.project_learning import initialize_learning

_BACKUP_PATHS = (
    "context/learning",
    "context/governance",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("project.json invalide")
    return payload


def detect_schema(project: Path) -> str:
    value = _load(project / "project.json").get("schema_version")
    return str(value or "1.1.0")


def plan_project_migration(project: Path) -> list[str]:
    schema = detect_schema(project)
    if schema == PROJECT_SCHEMA_VERSION:
        return []
    if schema == "1.1.0":
        return ["1.1.0->2.0.0"]
    raise ValueError(f"migration non définie pour le schéma {schema}")


def _backup(project: Path, source_schema: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    root = project / ".migrations" / f"pre-{source_schema}-{stamp}"
    root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(project / "project.json", root / "project.json")
    metadata: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_schema": source_schema,
        "paths": {},
    }
    paths = metadata["paths"]
    assert isinstance(paths, dict)
    for relative in _BACKUP_PATHS:
        source = project / relative
        paths[relative] = source.exists()
        if source.is_dir():
            shutil.copytree(source, root / relative)
        elif source.is_file():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    (root / "backup.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _restore_backup(project: Path, backup: Path) -> None:
    shutil.copy2(backup / "project.json", project / "project.json")
    metadata = _load(backup / "backup.json")
    paths = metadata.get("paths", {})
    if not isinstance(paths, dict):
        raise RuntimeError("backup migration invalide")
    for relative in _BACKUP_PATHS:
        target = project / relative
        if target.exists() or target.is_symlink():
            _remove_path(target)
        if paths.get(relative) is True:
            source = backup / relative
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def _append_ledger(project: Path, record: dict[str, Any]) -> None:
    ledger = project / ".migrations" / "ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _migrate_1_1_to_2_0(project: Path) -> None:
    old = _load(project / "project.json")
    created_at = str(old.get("created_at") or _now())
    payload = build_project_manifest(
        project_id=str(old.get("project_id") or project.name),
        title=str(old.get("title") or project.name),
        created_at=created_at,
        expected_deliverables=[str(item) for item in old.get("expected_deliverables", [])],
        source_items=[str(item) for item in old.get("source_items", [])],
        intake_items=[str(item) for item in old.get("intake_items", [])],
        intake_archive=str(old.get("intake_archive") or "legacy-unknown"),
        owner=str(old.get("owner") or "dirigeant-operateur"),
        classification=str(old.get("classification") or "internal"),
        criticality=str(old.get("criticality") or "standard"),
    )
    status = str(old.get("status") or "INTAKE_READY")
    payload["status"] = status
    payload["updated_at"] = str(old.get("updated_at") or _now())
    if isinstance(old.get("orchestration"), dict):
        payload["orchestration"] = old["orchestration"]
    validate_project_manifest(payload)
    (project / "project.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    initialize_governance(project)
    learning_root = project / "context" / "learning"
    if not (learning_root / "LEARNING_CONTRACT.json").exists():
        initialize_learning(project, preserve_existing=True)


def apply_project_migrations(project: Path) -> list[str]:
    steps = plan_project_migration(project)
    for step in steps:
        source, target = step.split("->", maxsplit=1)
        backup = _backup(project, source)
        try:
            if step == "1.1.0->2.0.0":
                _migrate_1_1_to_2_0(project)
            else:
                raise ValueError(f"étape inconnue: {step}")
            if detect_schema(project) != target:
                raise RuntimeError("validation post-migration échouée")
            validate_project_manifest(_load(project / "project.json"))
        except Exception as exc:
            try:
                _restore_backup(project, backup)
            except Exception as rollback_exc:
                raise RuntimeError("migration échouée et rollback impossible") from rollback_exc
            _append_ledger(
                project,
                {
                    "timestamp": _now(),
                    "source": source,
                    "target": target,
                    "backup": str(backup.relative_to(project)),
                    "status": "ROLLED_BACK",
                    "error_type": type(exc).__name__,
                },
            )
            raise
        _append_ledger(
            project,
            {
                "timestamp": _now(),
                "source": source,
                "target": target,
                "backup": str(backup.relative_to(project)),
                "status": "APPLIED",
            },
        )
    return steps


def ensure_current_project_schema(project: Path) -> None:
    apply_project_migrations(project)
    validate_project_manifest(_load(project / "project.json"))
