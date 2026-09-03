from __future__ import annotations

import shutil
from pathlib import Path

from clawlocal.project_intake import validate_project_id
from clawlocal.safe_fs import (
    assert_no_link_like,
    copytree_no_links,
    iter_regular_files_no_links,
    secure_path_within,
)
from clawlocal.workspace_guard import (
    allowed_output_kinds,
    validate_workspace_guard,
    write_workspace_guard,
)

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


def _workspace_guard_reference(
    platform_root: Path,
    project_id: str,
    agent_id: str,
) -> Path:
    return (
        platform_root
        / "state"
        / "workspace-guards"
        / project_id
        / f"{agent_id}.json"
    )


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
    manifest = project / "project.json"
    secure_path_within(manifest, project, require_file=True, label="manifest projet")

    target = platform_root / "workspaces" / agent_id / "projects" / normalized
    if target.exists():
        marker = target / _SNAPSHOT_MARKER
        if not marker.exists():
            raise FileExistsError(f"snapshot non géré, refus d'écraser: {target}")
        secure_path_within(marker, target, require_file=True, label="snapshot géré")
        shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=False)
    (target / _SNAPSHOT_MARKER).write_text(
        "managed-by=OPENCLAW_LOCAL\n",
        encoding="utf-8",
    )
    shutil.copy2(manifest, target / "project.json")
    for name in _CONTEXT_DIRS:
        source = project / name
        if source.exists():
            copytree_no_links(source, target / name, label=f"contexte {name}")

    for name in _OUTPUT_DIRS:
        source = project / name
        destination = target / name
        if include_outputs and source.exists():
            copytree_no_links(source, destination, label=f"sorties centrales {name}")
        else:
            destination.mkdir()

    assert_no_link_like(target, label="snapshot agent")
    reference = _workspace_guard_reference(platform_root, normalized, agent_id)
    write_workspace_guard(target, agent_id, reference_path=reference)
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
    marker = workspace_project / _SNAPSHOT_MARKER
    secure_path_within(marker, workspace_project, require_file=True, label="snapshot agent")
    reference = _workspace_guard_reference(platform_root, normalized, agent_id)
    validate_workspace_guard(
        workspace_project,
        agent_id,
        reference_path=reference,
    )

    project = platform_root / "projects" / normalized
    secure_path_within(project / "project.json", project, require_file=True, label="projet")

    collected: list[str] = []
    allowed_kinds = allowed_output_kinds(agent_id)
    for kind in _OUTPUT_DIRS:
        source = workspace_project / kind / normalized_task
        if not source.exists():
            continue
        if kind not in allowed_kinds:
            files = list(iter_regular_files_no_links(source, label=f"sortie interdite {kind}"))
            if files:
                raise PermissionError(
                    f"{agent_id}: sortie hors collect_scopes interdite: {kind}/{normalized_task}"
                )
            continue
        secure_path_within(source, workspace_project, require_dir=True, label="sortie tâche")
        files = list(iter_regular_files_no_links(source, label=f"sortie agent {kind}"))
        if not files:
            continue

        run_dir = _next_run_dir(
            project / kind / "tasks" / normalized_task / agent_id
        )
        for path in files:
            safe_source = secure_path_within(
                path,
                source,
                require_file=True,
                label="fichier de sortie agent",
            )
            relative = safe_source.relative_to(source.resolve(strict=True))
            destination = run_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_source, destination)
            collected.append(destination.relative_to(project).as_posix())

    return sorted(collected)
