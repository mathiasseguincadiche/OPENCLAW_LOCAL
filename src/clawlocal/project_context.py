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
_OUTPUT_DIRS = ("work", "deliverables", "evidence", "diagrams")
_SNAPSHOT_MARKER = ".openclaw-local-project-snapshot"


def sync_project_context(
    platform_root: Path,
    project_id: str,
    agent_id: str,
    *,
    include_outputs: bool = False,
) -> Path:
    normalized = validate_project_id(project_id)
    if agent_id not in AGENT_IDS:
        raise ValueError(f"agent inconnu: {agent_id}")

    project = platform_root / "projects" / normalized
    if not (project / "project.json").exists():
        raise FileNotFoundError(project / "project.json")

    target = platform_root / "workspaces" / agent_id / "projects" / normalized
    if target.exists():
        if not (target / _SNAPSHOT_MARKER).exists():
            raise FileExistsError(
                f"snapshot non géré, refus d'écraser: {target}"
            )
        shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=False)
    (target / _SNAPSHOT_MARKER).write_text(
        "managed-by=OPENCLAW_LOCAL\n",
        encoding="utf-8",
    )
    shutil.copy2(project / "project.json", target / "project.json")
    for name in _CONTEXT_DIRS:
        source = project / name
        if source.exists():
            shutil.copytree(source, target / name)

    for name in _OUTPUT_DIRS:
        source = project / name
        destination = target / name
        if include_outputs and source.exists():
            shutil.copytree(source, destination)
        else:
            destination.mkdir()

    return target


def sync_project_to_all_agents(
    platform_root: Path,
    project_id: str,
    *,
    include_outputs: bool = False,
) -> list[Path]:
    return [
        sync_project_context(
            platform_root,
            project_id,
            agent,
            include_outputs=include_outputs,
        )
        for agent in AGENT_IDS
    ]


def _next_run_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = base / f"run-{index:03d}"
        if not candidate.exists():
            candidate.mkdir()
            return candidate
        index += 1


def collect_agent_outputs(
    platform_root: Path,
    project_id: str,
    agent_id: str,
    task_id: str,
) -> list[str]:
    normalized = validate_project_id(project_id)
    normalized_task = validate_project_id(task_id)
    if agent_id not in AGENT_IDS:
        raise ValueError(f"agent inconnu: {agent_id}")

    workspace_project = (
        platform_root
        / "workspaces"
        / agent_id
        / "projects"
        / normalized
    )
    if not (workspace_project / _SNAPSHOT_MARKER).is_file():
        raise FileNotFoundError(
            f"snapshot agent absent ou non géré: {workspace_project}"
        )

    project = platform_root / "projects" / normalized
    if not (project / "project.json").is_file():
        raise FileNotFoundError(project / "project.json")

    collected: list[str] = []
    for kind in _OUTPUT_DIRS:
        source = workspace_project / kind / normalized_task
        if not source.exists():
            continue
        if source.is_file():
            raise ValueError(f"sortie tâche invalide, dossier attendu: {source}")
        files = [path for path in source.rglob("*") if path.is_file()]
        if not files:
            continue

        run_dir = _next_run_dir(
            project / kind / "tasks" / normalized_task / agent_id
        )
        for path in files:
            relative = path.relative_to(source)
            destination = run_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            collected.append(destination.relative_to(project).as_posix())

    return sorted(collected)
