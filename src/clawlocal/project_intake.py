from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

PROJECT_DIRS = (
    "intake",
    "sources",
    "context",
    "work",
    "deliverables",
    "evidence",
    "diagrams",
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


@dataclass(frozen=True)
class ProjectManifest:
    schema_version: str
    project_id: str
    title: str
    created_at: str
    status: str
    expected_deliverables: list[str]
    source_items: list[str]


def validate_project_id(project_id: str) -> str:
    value = project_id.strip().lower()
    if not _SLUG_RE.fullmatch(value):
        raise ValueError(
            "project_id invalide: utiliser 3-64 caractères [a-z0-9-], "
            "sans tiret en début/fin"
        )
    return value


def _safe_destination(root: Path, project_id: str) -> Path:
    projects_root = (root / "projects").resolve()
    destination = (projects_root / project_id).resolve()
    if destination.parent != projects_root:
        raise ValueError("destination projet hors racine autorisée")
    return destination


def _copy_items(items: Iterable[Path], destination: Path) -> list[str]:
    copied: list[str] = []
    for item in items:
        source = item.expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        target = destination / source.name
        if target.exists():
            raise FileExistsError(target)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        copied.append(source.name)
    return copied


def create_project(
    platform_root: Path,
    project_id: str,
    title: str,
    *,
    intake_items: Iterable[Path] = (),
    source_items: Iterable[Path] = (),
    expected_deliverables: Iterable[str] = (),
) -> Path:
    normalized_id = validate_project_id(project_id)
    destination = _safe_destination(platform_root, normalized_id)
    if destination.exists():
        raise FileExistsError(destination)

    for name in PROJECT_DIRS:
        (destination / name).mkdir(parents=True, exist_ok=False if name == PROJECT_DIRS[0] else True)

    copied_intake = _copy_items(intake_items, destination / "intake")
    copied_sources = _copy_items(source_items, destination / "sources")
    deliverables = [value.strip() for value in expected_deliverables if value.strip()]

    manifest = ProjectManifest(
        schema_version="1.0.0",
        project_id=normalized_id,
        title=title.strip() or normalized_id,
        created_at=datetime.now(UTC).isoformat(),
        status="INTAKE_READY",
        expected_deliverables=deliverables,
        source_items=copied_sources,
    )
    payload = asdict(manifest)
    payload["intake_items"] = copied_intake
    (destination / "project.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
