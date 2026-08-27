from __future__ import annotations

import shutil
from pathlib import Path

from clawlocal.project_intake import validate_project_id

AGENT_IDS = (
    "chef-operations",
    "expert-recherche",
    "architecte-solutions",
    "ingenieur-devops",
    "ingenieur-securite",
    "ingenieur-release-forges",
    "redacteur-technique",
    "auditeur-qualite",
)

_CONTEXT_DIRS = ("intake", "sources", "context")


def sync_project_context(platform_root: Path, project_id: str, agent_id: str) -> Path:
    normalized = validate_project_id(project_id)
    if agent_id not in AGENT_IDS:
        raise ValueError(f"agent inconnu: {agent_id}")

    project = platform_root / "projects" / normalized
    if not (project / "project.json").exists():
        raise FileNotFoundError(project / "project.json")

    target = platform_root / "workspaces" / agent_id / "projects" / normalized
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(project / "project.json", target / "project.json")
    for name in _CONTEXT_DIRS:
        source = project / name
        if source.exists():
            shutil.copytree(source, target / name)
    (target / "work").mkdir()
    (target / "deliverables").mkdir()
    (target / "evidence").mkdir()
    (target / "diagrams").mkdir()
    return target


def sync_project_to_all_agents(platform_root: Path, project_id: str) -> list[Path]:
    return [sync_project_context(platform_root, project_id, agent) for agent in AGENT_IDS]
