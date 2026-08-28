from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml

_REPOSITORY_ROOT_ENV = "OPENCLAW_LOCAL_REPO_ROOT"


def _is_repository_root(path: Path) -> bool:
    return (
        (path / "config" / "v1" / "platform.yaml").is_file()
        and (path / "config" / "v1" / "model_catalog.yaml").is_file()
        and (path / "pyproject.toml").is_file()
    )


def _find_repository_from(anchor: Path) -> Path | None:
    resolved = anchor.expanduser().resolve()
    start = resolved if resolved.is_dir() else resolved.parent
    for candidate in (start, *start.parents):
        if _is_repository_root(candidate):
            return candidate
    return None


def repository_root() -> Path:
    explicit = os.environ.get(_REPOSITORY_ROOT_ENV)
    if explicit:
        explicit_root = Path(explicit).expanduser().resolve()
        if not _is_repository_root(explicit_root):
            raise FileNotFoundError(
                f"{_REPOSITORY_ROOT_ENV} pointe vers un dépôt OPENCLAW_LOCAL invalide: "
                f"{explicit_root}"
            )
        return explicit_root

    anchors = [Path.cwd()]
    if sys.argv and sys.argv[0]:
        anchors.append(Path(sys.argv[0]))
    anchors.append(Path(__file__))

    for anchor in anchors:
        discovered_root = _find_repository_from(anchor)
        if discovered_root is not None:
            return discovered_root

    raise FileNotFoundError(
        "Racine du dépôt OPENCLAW_LOCAL introuvable. "
        f"Définissez {_REPOSITORY_ROOT_ENV} vers le clone contenant config\\v1."
    )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration invalide: {path}")
    return data


def load_contract(name: str) -> dict[str, Any]:
    return load_yaml(repository_root() / "config" / "v1" / name)
