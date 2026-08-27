import json
import os
from pathlib import Path

import pytest

from clawlocal.project_intake import create_project, validate_project_id


def test_validate_project_id() -> None:
    assert validate_project_id("P4-DevOps") == "p4-devops"
    with pytest.raises(ValueError):
        validate_project_id("../escape")


def test_create_project_materializes_integrity_and_learning(tmp_path: Path) -> None:
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
    assert (project / "intake" / "MANIFEST.json").exists()
    assert (project / "intake" / "checksums.sha256").exists()
    assert (project / "intake" / "mime-types.tsv").exists()
    assert (project / "intake" / "INGESTION_REPORT.md").exists()
    assert (project / "sources" / "repo" / "README.md").exists()
    assert (project / "context" / "PROJECT_GUIDANCE.md").exists()
    assert (project / "context" / "learning" / "SKILLS_MATRIX.csv").exists()
    assert (project / "context" / "publication.json").exists()

    manifest = json.loads((project / "intake" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["immutable"] is True
    assert manifest["files"][0]["path"] == "consignes.md"
    assert len(manifest["files"][0]["sha256"]) == 64
    if os.name != "nt":
        assert not bool((project / "intake" / "consignes.md").stat().st_mode & 0o200)


def test_create_project_refuses_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    create_project(root, "demo-projet", "Demo")
    with pytest.raises(FileExistsError):
        create_project(root, "demo-projet", "Demo")


def test_create_project_refuses_suspected_secret_before_materialization(
    tmp_path: Path,
) -> None:
    intake = tmp_path / "notes.md"
    intake.write_text("api_key = super-secret-token-123", encoding="utf-8")
    root = tmp_path / "platform"
    with pytest.raises(ValueError, match="secret potentiel"):
        create_project(root, "secret-demo", "Secret Demo", intake_items=[intake])
    assert not (root / "projects" / "secret-demo").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink indisponible")
def test_create_project_refuses_symlink_in_intake(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("création de symlink non autorisée sur ce runner")
    with pytest.raises(ValueError, match="lien symbolique interdit"):
        create_project(
            tmp_path / "platform",
            "symlink-demo",
            "Symlink Demo",
            intake_items=[link],
        )
