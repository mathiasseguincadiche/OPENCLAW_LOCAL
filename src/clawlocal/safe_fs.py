from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import Iterator


def is_link_like(path: Path) -> bool:
    """Return True for symlinks and Windows reparse-point based links/junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    if os.name != "nt":
        return False
    attributes = int(getattr(info, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    if attributes & reparse_flag:
        return True
    is_junction = getattr(os.path, "isjunction", None)
    return bool(is_junction and is_junction(path))


def assert_no_link_like(root: Path, *, label: str = "arborescence") -> None:
    """Fail closed if root contains a symlink, junction or other reparse point."""
    if is_link_like(root):
        raise ValueError(f"{label}: lien/reparse point interdit: {root}")
    if not root.exists() or not root.is_dir():
        return

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in [*dirnames, *filenames]:
            candidate = current_path / name
            if is_link_like(candidate):
                raise ValueError(f"{label}: lien/reparse point interdit: {candidate}")


def secure_path_within(
    path: Path,
    root: Path,
    *,
    require_file: bool = False,
    require_dir: bool = False,
    label: str = "chemin",
) -> Path:
    """Validate lexical/resolved containment and reject link-like path components."""
    root_absolute = root.absolute()
    candidate_absolute = path.absolute()
    try:
        relative = candidate_absolute.relative_to(root_absolute)
    except ValueError as exc:
        raise ValueError(f"{label}: chemin hors racine autorisée: {path}") from exc

    current = root_absolute
    if is_link_like(current):
        raise ValueError(f"{label}: racine liée/reparse point interdite: {root}")
    for part in relative.parts:
        current = current / part
        if is_link_like(current):
            raise ValueError(f"{label}: lien/reparse point interdit: {current}")

    root_resolved = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"{label}: résolution hors racine autorisée: {path}")
    if require_file and not resolved.is_file():
        raise FileNotFoundError(path)
    if require_dir and not resolved.is_dir():
        raise NotADirectoryError(path)
    return resolved


def iter_regular_files_no_links(root: Path, *, label: str = "arborescence") -> Iterator[Path]:
    assert_no_link_like(root, label=label)
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file():
            secure_path_within(path, root, require_file=True, label=label)
            yield path


def copytree_no_links(source: Path, destination: Path, *, label: str = "source") -> None:
    assert_no_link_like(source, label=label)
    shutil.copytree(source, destination, symlinks=False)
    assert_no_link_like(destination, label=f"copie {label}")
