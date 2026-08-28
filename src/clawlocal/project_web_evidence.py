from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.web_evidence import validate_web_evidence_file


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON invalide: {path}")
    return payload


def _plan(project: Path) -> dict[str, Any]:
    path = project / "context" / "project_plan.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return _load_json(path)


def _markers() -> tuple[str, str]:
    policy = load_contract("web_policy.yaml")
    enforcement = policy.get("project_enforcement", {})
    web_marker = str(enforcement.get("web_required_evidence_marker", "")).strip()
    runtime_marker = str(
        enforcement.get("runtime_required_evidence_marker", "")
    ).strip()
    if not web_marker or not runtime_marker:
        raise ValueError("web_policy.yaml: marqueurs required_evidence incomplets")
    return web_marker, runtime_marker


def task_web_evidence_requirements(
    project: Path,
    task_id: str,
) -> tuple[bool, bool]:
    tasks = _plan(project).get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("project_plan.json: tasks invalide")
    task = next(
        (
            item
            for item in tasks
            if isinstance(item, dict) and str(item.get("id", "")) == task_id
        ),
        None,
    )
    if task is None:
        raise KeyError(f"tâche inconnue dans project_plan.json: {task_id}")
    required = task.get("required_evidence", [])
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise ValueError(f"{task_id}: required_evidence invalide")
    web_marker, runtime_marker = _markers()
    values = {item.strip() for item in required}
    require_web = web_marker in values
    require_runtime = runtime_marker in values
    if require_runtime and not require_web:
        raise ValueError(
            f"{task_id}: {runtime_marker} exige aussi {web_marker} dans required_evidence"
        )
    return require_web, require_runtime


def task_web_evidence_failures(project: Path, task_id: str) -> list[str]:
    try:
        require_web, require_runtime = task_web_evidence_requirements(project, task_id)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        return [str(exc)]
    if not require_web:
        return []
    path = project / "evidence" / task_id / "web_evidence.json"
    try:
        validate_web_evidence_file(
            path,
            expected_task_id=task_id,
            require_runtime=require_runtime,
        )
    except (FileNotFoundError, ValueError) as exc:
        return [f"{task_id}: {exc}"]
    return []


def project_web_evidence_failures(project: Path) -> list[str]:
    try:
        tasks = _plan(project).get("tasks", [])
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    if not isinstance(tasks, list):
        return ["project_plan.json: tasks invalide"]
    failures: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            failures.append("project_plan.json: tâche invalide")
            continue
        task_id = str(task.get("id", "")).strip()
        if not task_id:
            failures.append("project_plan.json: tâche sans id")
            continue
        failures.extend(task_web_evidence_failures(project, task_id))
    return failures
