from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract

_ASSIGNMENTS = Path("context/task_assignments.json")
_VALID_SOURCES = {"validation", "review"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON invalide: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _finding_task_ids(report: dict[str, Any]) -> list[str]:
    values: list[str] = []
    findings = report.get("findings", report.get("blocking_findings", []))
    if not isinstance(findings, list):
        return values
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        task_id = finding.get("task_id")
        if task_id:
            values.append(str(task_id))
        task_ids = finding.get("task_ids", [])
        if isinstance(task_ids, list):
            values.extend(str(value) for value in task_ids if str(value).strip())
    return values


def _requested_task_ids(report: dict[str, Any]) -> list[str]:
    explicit = report.get("retry_task_ids")
    if explicit is not None:
        if not isinstance(explicit, list):
            raise ValueError("retry_task_ids doit être une liste")
        return [str(value) for value in explicit if str(value).strip()]
    return _finding_task_ids(report)


def _dependent_closure(
    requested: set[str],
    tasks_by_id: dict[str, dict[str, Any]],
) -> set[str]:
    impacted = set(requested)
    changed = True
    while changed:
        changed = False
        for task_id, task in tasks_by_id.items():
            dependencies = {str(value) for value in task.get("depends_on", [])}
            if task_id not in impacted and dependencies & impacted:
                impacted.add(task_id)
                changed = True
    return impacted


def _history_path(project: Path, remediation_policy: dict[str, Any]) -> Path:
    relative = Path(str(remediation_policy.get("history_path", "")))
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[0] != "evidence"
    ):
        raise ValueError("orchestration_policy.yaml: history_path remediation invalide")
    return project / relative


def reopen_tasks_for_correction(
    project: Path,
    report: dict[str, Any],
    *,
    source: str,
) -> list[str]:
    if source not in _VALID_SOURCES:
        raise ValueError(f"source de remediation inconnue: {source}")
    if str(report.get("verdict", "")).upper() != "FAIL":
        return []

    assignments_path = project / _ASSIGNMENTS
    assignments = _load_json(assignments_path)
    tasks = assignments.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("task_assignments.json: tasks invalide")

    tasks_by_id = {
        str(task.get("task_id")): task
        for task in tasks
        if isinstance(task, dict) and str(task.get("task_id", "")).strip()
    }
    if len(tasks_by_id) != len(tasks):
        raise ValueError("task_assignments.json: task_id invalide ou dupliqué")

    requested_values = _requested_task_ids(report)
    fallback_all = not requested_values
    requested = set(requested_values) if requested_values else set(tasks_by_id)
    unknown = sorted(requested - set(tasks_by_id))
    if unknown:
        raise ValueError(f"tâches de correction inconnues: {', '.join(unknown)}")

    policy = load_contract("orchestration_policy.yaml")
    remediation = policy.get("remediation", {})
    if remediation.get("reopen_failed_tasks") is not True:
        raise RuntimeError("remediation désactivée par contrat")
    include_dependents = remediation.get("reopen_transitive_dependents", True) is True
    impacted = (
        _dependent_closure(requested, tasks_by_id)
        if include_dependents
        else requested
    )

    max_attempts = int(policy.get("execution", {}).get("max_task_attempts", 2))
    exhausted = sorted(
        task_id
        for task_id in impacted
        if int(tasks_by_id[task_id].get("attempts", 0)) >= max_attempts
    )
    if exhausted:
        raise RuntimeError(
            "limite de tentatives atteinte; intervention humaine requise: "
            + ", ".join(exhausted)
        )

    now = _now()
    reopened = sorted(impacted)
    for task_id in reopened:
        task = tasks_by_id[task_id]
        task["previous_status"] = task.get("status")
        task["status"] = "PENDING"
        task["reopened_at"] = now
        task["reopened_by"] = source
        task["correction_cycle"] = int(task.get("correction_cycle", 0)) + 1

    assignments["updated_at"] = now
    _write_json(assignments_path, assignments)

    history_path = _history_path(project, remediation)
    if history_path.is_file():
        history = _load_json(history_path)
    else:
        history = {"schema_version": "1.0.0", "events": []}
    events = history.setdefault("events", [])
    if not isinstance(events, list):
        raise ValueError("remediation_history.json: events invalide")
    events.append(
        {
            "at": now,
            "source": source,
            "requested_task_ids": sorted(requested),
            "reopened_task_ids": reopened,
            "fallback_all_tasks": fallback_all,
            "transitive_dependents": include_dependents,
        }
    )
    history["updated_at"] = now
    _write_json(history_path, history)
    return reopened
