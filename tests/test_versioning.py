from __future__ import annotations

from pathlib import Path

import pytest

from clawlocal.versioning import repository_version, validate_release_tag, validate_semver

ROOT = Path(__file__).resolve().parents[1]


def current_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_repository_version_is_consistent() -> None:
    assert repository_version(ROOT) == current_version()


def test_release_tag_matches_repository_version() -> None:
    version = current_version()
    assert validate_release_tag(ROOT, f"v{version}") == version


def test_release_tag_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="tag attendu"):
        validate_release_tag(ROOT, "v999.0.0")


@pytest.mark.parametrize("value", ["1", "01.2.3", "v1.2.3", "1.2", "1.2.3.4"])
def test_invalid_semver_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        validate_semver(value)
