import os
from pathlib import Path

import pytest

from clawlocal.project_intake import create_project, validate_project_id


def test_validate_project_id() -> None:
    assert validate_project_id("P4-DevOps") == "p4-devops"
    with pytest.raises(ValueError):
        validate_project_id("../escape")


def test_create_project_materializes_hardened_contract(tmp_path: Path) -> None:
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
    evidence = project / "evidence" / "intake"
    assert (evidence / "manifest.json").is_file()
    assert "consignes.md" in (evidence / "checksums.sha256").read_text(
        encoding="utf-8"
    )
    assert "text/markdown" in (evidence / "mime-types.tsv").read_text(
        encoding="utf-8"
    )
    assert (evidence / "INGESTION_REPORT.md").is_file()
    assert (project / "context" / "learning" / "SKILLS_MATRIX.csv").is_file()
    assert (project / "context" / "publication" / "publication.json").is_file()


def test_create_project_refuses_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    create_project(root, "demo-projet", "Demo")
    with pytest.raises(FileExistsError):
        create_project(root, "demo-projet", "Demo")


def test_create_project_refuses_secret_before_materialization(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    intake = tmp_path / ".env"
    intake.write_text("OPENAI_API_KEY=abcdefghijk", encoding="utf-8")
    with pytest.raises(ValueError):
        create_project(root, "secret-demo", "Secret Demo", intake_items=[intake])
    assert not (root / "projects" / "secret-demo").exists()


def test_create_project_refuses_intake_symlink(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("création de symlink Windows dépend des privilèges du runner")
    target = tmp_path / "target.md"
    target.write_text("source", encoding="utf-8")
    link = tmp_path / "link.md"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        create_project(
            tmp_path / "platform",
            "symlink-demo",
            "Symlink Demo",
            intake_items=[link],
        )
