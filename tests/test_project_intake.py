from pathlib import Path

import pytest

from clawlocal.project_intake import create_project, validate_project_id


def test_validate_project_id() -> None:
    assert validate_project_id("P4-DevOps") == "p4-devops"
    with pytest.raises(ValueError):
        validate_project_id("../escape")


def test_create_project_materializes_contract(tmp_path: Path) -> None:
    intake = tmp_path / "consignes.md"
    intake.write_text("Consignes", encoding="utf-8")
    source = tmp_path / "repo"
    source.mkdir()
    (source / "README.md").write_text("Projet", encoding="utf-8")
    project = create_project(
        tmp_path / "platform",
        "p4-devops",
        "Projet P4",
        intake_items=[intake],
        source_items=[source],
        expected_deliverables=["README", "pipeline"],
    )
    assert (project / "project.json").exists()
    assert (project / "intake" / "consignes.md").exists()
    assert (project / "sources" / "repo" / "README.md").exists()
    assert (project / "deliverables").is_dir()
    assert (project / "evidence").is_dir()


def test_create_project_refuses_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    create_project(root, "demo-projet", "Demo")
    with pytest.raises(FileExistsError):
        create_project(root, "demo-projet", "Demo")
