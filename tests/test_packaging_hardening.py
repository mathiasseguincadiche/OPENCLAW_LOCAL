from __future__ import annotations

from pathlib import Path

import pytest

from clawlocal.project_intake import create_project
from clawlocal.project_orchestrator import package_project


def _require_symlink_support(tmp_path: Path) -> None:
    target = tmp_path / "symlink-probe-target"
    link = tmp_path / "symlink-probe-link"
    target.write_text("probe", encoding="utf-8")
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("création de symlink non autorisée sur ce runner")
    finally:
        link.unlink(missing_ok=True)
        target.unlink(missing_ok=True)


def test_base_package_project_rejects_linked_deliverable(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    project = create_project(tmp_path / "platform", "package-link", "Package Link")
    deliverables = project / "deliverables"
    (deliverables / "README.md").write_text("# Safe\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("PRIVATE", encoding="utf-8")
    (deliverables / "escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="lien|reparse"):
        package_project(project)

    assert not (deliverables / "package-link.zip").exists()


def test_base_package_project_rejects_linked_manifest_target(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    project = create_project(tmp_path / "platform", "package-manifest", "Package Manifest")
    deliverables = project / "deliverables"
    (deliverables / "README.md").write_text("# Safe\n", encoding="utf-8")
    outside = tmp_path / "outside-manifest.json"
    outside.write_text("{}", encoding="utf-8")
    (deliverables / "package_manifest.json").symlink_to(outside)

    with pytest.raises(ValueError, match="lien|reparse"):
        package_project(project)

    assert outside.read_text(encoding="utf-8") == "{}"
