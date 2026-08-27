from __future__ import annotations

import re
import tomllib
from pathlib import Path

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"$', re.MULTILINE)


def validate_semver(value: str) -> str:
    version = value.strip()
    if not SEMVER.fullmatch(version):
        raise ValueError(f"version SemVer invalide: {value!r}")
    return version


def repository_version(root: Path) -> str:
    version = validate_semver(
        (root / "VERSION").read_text(encoding="utf-8")
    )

    with (root / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    package_version = validate_semver(
        str(pyproject["project"]["version"])
    )
    if package_version != version:
        raise ValueError(
            f"VERSION={version} mais pyproject.toml project.version="
            f"{package_version}"
        )

    init_text = (
        root / "src" / "clawlocal" / "__init__.py"
    ).read_text(encoding="utf-8")
    match = _INIT_VERSION_RE.search(init_text)
    if not match:
        raise ValueError("src/clawlocal/__init__.py ne déclare pas __version__")
    init_version = validate_semver(match.group(1))
    if init_version != version:
        raise ValueError(
            f"VERSION={version} mais clawlocal.__version__={init_version}"
        )

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        raise ValueError(
            f"CHANGELOG.md ne contient pas de section [{version}]"
        )
    return version


def validate_release_tag(root: Path, tag: str | None) -> str:
    version = repository_version(root)
    if tag is None:
        return version
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(f"tag attendu {expected}, reçu {tag}")
    return version
