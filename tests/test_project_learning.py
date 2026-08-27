from pathlib import Path

import pytest

from clawlocal.project_learning import initialize_learning_context, record_learning


def test_initialize_learning_context_materializes_guidance(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "context").mkdir(parents=True)
    root = initialize_learning_context(project, "balanced")
    assert (root / "profile.json").exists()
    assert (root / "SKILLS_MATRIX.csv").exists()
    assert (root / "LEARNING_JOURNAL.md").exists()
    assert (root / "TEACH_BACK.md").exists()
    assert (root / "RETENTION_PLAN.yaml").exists()
    guidance = (project / "context" / "PROJECT_GUIDANCE.md").read_text(encoding="utf-8")
    assert "balanced" in guidance
    assert "Comprendre" in guidance
    assert "Diagnostiquer" in guidance


def test_acquired_requires_explicit_validation(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "context").mkdir(parents=True)
    initialize_learning_context(project)
    with pytest.raises(PermissionError):
        record_learning(project, skill="terraform", status="ACQUIRED")
    record_learning(
        project,
        skill="terraform",
        status="ACQUIRED",
        evidence="evaluation-001",
        human_validated=True,
    )
    matrix = (project / "context" / "learning" / "SKILLS_MATRIX.csv").read_text(
        encoding="utf-8"
    )
    assert "terraform,ACQUIRED,evaluation-001" in matrix
