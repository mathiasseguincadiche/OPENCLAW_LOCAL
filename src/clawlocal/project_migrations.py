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
from clawlocal.project_ingestion import ingest_project_documents, validate_ingestion_index
from clawlocal.project_learning import initialize_learning
from clawlocal.safe_fs import (
    assert_no_link_like,
    copytree_no_links,
    is_link_like,
    secure_path_within,
)

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


def _migrations_root(project: Path, *, create: bool) -> Path:
    project_root = project.resolve(strict=True)
    root = project_root / ".migrations"
    if root.exists() or is_link_like(root):
        return secure_path_within(
            root,
            project_root,
            require_dir=True,
            label="répertoire de migrations",
        )
    if not create:
        raise FileNotFoundError(root)
    root.mkdir()
    return secure_path_within(
        root,
        project_root,
        require_dir=True,
        label="répertoire de migrations",
    )


def _backup(project: Path, source_schema: str) -> Path:
    project_root = project.resolve(strict=True)
    manifest = secure_path_within(
        project_root / "project.json",
        project_root,
        require_file=True,
        label="manifest de migration",
    )

    sources: dict[str, Path | None] = {}
    present: dict[str, bool] = {}
    for relative in _BACKUP_PATHS:
        source = project_root / relative
        if not source.exists() and not is_link_like(source):
            present[relative] = False
            sources[relative] = None
            continue
        safe_source = secure_path_within(
            source,
            project_root,
            label=f"backup migration {relative}",
        )
        if safe_source.is_dir():
            assert_no_link_like(safe_source, label=f"backup migration {relative}")
        elif not safe_source.is_file():
            raise ValueError(f"backup migration: type non supporté: {relative}")
        present[relative] = True
        sources[relative] = safe_source

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    root = _migrations_root(project_root, create=True) / f"pre-{source_schema}-{stamp}"
    root.mkdir(exist_ok=False)
    metadata: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_schema": source_schema,
        "paths": present,
    }
    try:
        shutil.copy2(manifest, root / "project.json")
        for relative, backup_source in sources.items():
            if backup_source is None:
                continue
            if backup_source.is_dir():
                copytree_no_links(
                    backup_source,
                    root / relative,
                    label=f"backup migration {relative}",
                )
            elif backup_source.is_file():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_source, target)
        (root / "backup.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def _remove_path(path: Path) -> None:
    if is_link_like(path):
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
        else:
            path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _restore_backup(project: Path, backup: Path) -> None:
    project_root = project.resolve(strict=True)
    migrations_root = _migrations_root(project_root, create=False)
    backup_root = secure_path_within(
        backup,
        migrations_root,
        require_dir=True,
        label="backup de migration",
    )
    assert_no_link_like(backup_root, label="backup de migration")
    manifest = secure_path_within(
        backup_root / "project.json",
        backup_root,
        require_file=True,
        label="manifest de rollback",
    )
    metadata_path = secure_path_within(
        backup_root / "backup.json",
        backup_root,
        require_file=True,
        label="métadonnées de rollback",
    )
    context_root = secure_path_within(
        project_root / "context",
        project_root,
        require_dir=True,
        label="contexte de rollback",
    )

    target_manifest = project_root / "project.json"
    if is_link_like(target_manifest):
        raise ValueError("rollback migration: project.json est un lien/reparse point")
    shutil.copy2(manifest, target_manifest)
    metadata = _load(metadata_path)
    paths = metadata.get("paths", {})
    if not isinstance(paths, dict):
        raise RuntimeError("backup migration invalide")
    for relative in _BACKUP_PATHS:
        target = project_root / relative
        if target.exists() or is_link_like(target):
            if not is_link_like(target):
                secure_path_within(target, context_root, label=f"rollback {relative}")
            _remove_path(target)
        if paths.get(relative) is True:
            source = secure_path_within(
                backup_root / relative,
                backup_root,
                label=f"source rollback {relative}",
            )
            if source.is_dir():
                copytree_no_links(
                    source,
                    target,
                    label=f"restore migration {relative}",
                )
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def _append_ledger(project: Path, record: dict[str, Any]) -> None:
    ledger = _migrations_root(project, create=True) / "ledger.jsonl"
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
                    "backup": str(backup.relative_to(project.resolve(strict=True))),
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
                "backup": str(backup.relative_to(project.resolve(strict=True))),
                "status": "APPLIED",
            },
        )
    return steps


def ensure_current_project_schema(project: Path) -> None:
    apply_project_migrations(project)
    validate_project_manifest(_load(project / "project.json"))
    ingestion_index = project / "context" / "ingestion" / "index.json"
    if ingestion_index.is_file():
        validate_ingestion_index(project)
    else:
        ingest_project_documents(project)
