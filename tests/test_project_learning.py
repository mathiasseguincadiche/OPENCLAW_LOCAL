import json
from pathlib import Path

from clawlocal.project_intake import create_project
from clawlocal.project_learning import (
    append_learning_entry,
    set_learning_profile,
    update_skill,
)


def test_project_initializes_learning_artifacts(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "learning-demo", "Learning Demo")
    root = project / "context" / "learning"
    assert (root / "SKILLS_MATRIX.csv").is_file()
    assert (root / "LEARNING_JOURNAL.md").is_file()
    assert (root / "TEACH_BACK.md").is_file()
    assert (root / "RETENTION_PLAN.yaml").is_file()
    assert (project / "context" / "documentation_profile.json").is_file()

    append_learning_entry(
        project,
        title="Terraform plan",
        understanding="Le plan prévisualise les changements.",
        evidence="terraform plan exécuté avec succès",
    )
    update_skill(
        project,
        skill="terraform",
        status="IN_PROGRESS",
        evidence="plan validé",
    )
    journal_before = (root / "LEARNING_JOURNAL.md").read_text(encoding="utf-8")
    set_learning_profile(project, profile="intensive", mode="evaluation")
    profile = json.loads((root / "learning_profile.json").read_text(encoding="utf-8"))

    assert profile["profile"] == "intensive"
    assert profile["mode"] == "evaluation"
    assert profile["execution_share_percent"] == 60
    assert journal_before == (root / "LEARNING_JOURNAL.md").read_text(encoding="utf-8")
    assert "terraform,IN_PROGRESS" in (root / "SKILLS_MATRIX.csv").read_text(
        encoding="utf-8"
    )
