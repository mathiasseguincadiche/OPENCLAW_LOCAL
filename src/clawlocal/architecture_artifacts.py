from __future__ import annotations

from pathlib import Path

_ALLOWED_ROOTS = {
    "architecture": Path("context/architecture"),
    "diagram": Path("diagrams"),
}


def write_architecture_artifact(
    project: Path,
    *,
    kind: str,
    relative_path: str,
    content: str,
) -> Path:
    if kind not in _ALLOWED_ROOTS:
        raise ValueError(f"type d'artefact architecture inconnu: {kind}")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("chemin d'artefact architecture non sûr")
    if not relative.parts:
        raise ValueError("chemin d'artefact architecture vide")

    root = (project / _ALLOWED_ROOTS[kind]).resolve()
    target = (root / relative).resolve()
    if root not in target.parents:
        raise ValueError("artefact architecture hors scope")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
