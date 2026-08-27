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
_SECRET_ASSIGNMENT_RE = re.compile(
    r"""(?im)^\s*(?:OPENROUTER_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|"""
    r"""AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN)\s*[:=]\s*["']?[A-Za-z0-9_./+=-]{8,}"""
)
_BLOCKED_SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
}
_BLOCKED_SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
_TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".ps1",
    ".sh",
}
_MAX_SECRET_SCAN_BYTES = 2 * 1024 * 1024


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


def _iter_files(item: Path) -> Iterable[Path]:
    if item.is_file():
        yield item
        return
    if item.is_dir():
        yield from (path for path in item.rglob("*") if path.is_file())


def _assert_intake_has_no_obvious_secret(item: Path) -> None:
    for path in _iter_files(item):
        if (
            path.name.casefold() in _BLOCKED_SECRET_NAMES
            or path.suffix.casefold() in _BLOCKED_SECRET_SUFFIXES
        ):
            raise ValueError(f"secret potentiel interdit dans l'intake: {path.name}")
        if path.suffix.casefold() not in _TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > _MAX_SECRET_SCAN_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if _SECRET_ASSIGNMENT_RE.search(text):
            raise ValueError(f"secret potentiel interdit dans l'intake: {path.name}")


def _copy_items(
    items: Iterable[Path],
    destination: Path,
    *,
    scan_secrets: bool = False,
) -> list[str]:
    copied: list[str] = []
    for item in items:
        source = item.expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        if scan_secrets:
            _assert_intake_has_no_obvious_secret(source)
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
        (destination / name).mkdir(
            parents=True,
            exist_ok=False if name == PROJECT_DIRS[0] else True,
        )

    copied_intake = _copy_items(
        intake_items,
        destination / "intake",
        scan_secrets=True,
    )
    copied_sources = _copy_items(source_items, destination / "sources")
    deliverables = [
        value.strip()
        for value in expected_deliverables
        if value.strip()
    ]

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
