from pathlib import Path

from clawlocal.project_context import AGENT_IDS, sync_project_to_all_agents
from clawlocal.project_intake import create_project


def test_sync_project_to_all_agents(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    note = tmp_path / "consignes.md"
    note.write_text("Consignes", encoding="utf-8")
    create_project(root, "projet-test", "Projet", intake_items=[note])
    targets = sync_project_to_all_agents(root, "projet-test")
    assert len(targets) == len(AGENT_IDS)
    for target in targets:
        assert (target / "project.json").exists()
        assert (target / "intake" / "consignes.md").exists()
        assert (target / "work").is_dir()
