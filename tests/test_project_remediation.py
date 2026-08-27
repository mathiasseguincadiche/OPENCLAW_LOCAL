import json
from pathlib import Path

import pytest

from clawlocal.project_intake import create_project
from clawlocal.project_orchestrator import create_assignments, record_task_result, store_plan
from clawlocal.project_remediation import reopen_tasks_for_correction


def _plan() -> dict[str, object]:
    return {
        "workstreams": ["delivery"],
        "tasks": [
            {
                "id": "task-001",
                "title": "Créer l'infrastructure",
                "role": "ingenieur-devops",
                "objective": "Produire Terraform",
                "depends_on": [],
                "expected_outputs": ["main.tf"],
                "acceptance_criteria": ["terraform validate"],
                "needs_web": False,
                "security_sensitive": False,
            },
            {
                "id": "task-002",
                "title": "Documenter l'infrastructure",
                "role": "redacteur-technique",
                "objective": "Produire le README",
                "depends_on": ["task-001"],
                "expected_outputs": ["README.md"],
                "acceptance_criteria": ["README cohérent"],
                "needs_web": False,
                "security_sensitive": False,
            },
        ],
    }


def _prepare_completed_assignments(tmp_path: Path) -> Path:
    root = tmp_path / "platform"
    project = create_project(root, "projet-test", "Projet")
    store_plan(project, _plan())
    create_assignments(project)
    record_task_result(
        project,
        "task-001",
        agent="ingenieur-devops",
        success=True,
        returncode=0,
        evidence_file="evidence/run-001.json",
        collected_outputs=["deliverables/task-001/main.tf"],
    )
    record_task_result(
        project,
        "task-002",
        agent="redacteur-technique",
        success=True,
        returncode=0,
        evidence_file="evidence/run-001.json",
        collected_outputs=["deliverables/task-002/README.md"],
    )
    return project


def _assignments(project: Path) -> dict[str, object]:
    return json.loads(
        (project / "context" / "task_assignments.json").read_text(encoding="utf-8")
    )


def test_validation_failure_reopens_target_and_dependents(tmp_path: Path) -> None:
    project = _prepare_completed_assignments(tmp_path)

    reopened = reopen_tasks_for_correction(
        project,
        {
            "verdict": "FAIL",
            "findings": [{"task_id": "task-001", "message": "Terraform invalide"}],
            "retry_task_ids": ["task-001"],
        },
        source="validation",
    )

    assert reopened == ["task-001", "task-002"]
    payload = _assignments(project)
    tasks = {task["task_id"]: task for task in payload["tasks"]}
    assert tasks["task-001"]["status"] == "PENDING"
    assert tasks["task-002"]["status"] == "PENDING"
    assert tasks["task-001"]["attempts"] == 1
    assert tasks["task-002"]["attempts"] == 1
    assert tasks["task-001"]["correction_cycle"] == 1

    history = json.loads(
        (project / "evidence" / "remediation_history.json").read_text(encoding="utf-8")
    )
    assert history["events"][-1]["reopened_task_ids"] == ["task-001", "task-002"]
    assert history["events"][-1]["fallback_all_tasks"] is False


def test_unmapped_failure_reopens_all_tasks_fail_closed(tmp_path: Path) -> None:
    project = _prepare_completed_assignments(tmp_path)

    reopened = reopen_tasks_for_correction(
        project,
        {"verdict": "FAIL", "findings": ["Livrable incohérent"]},
        source="review",
    )

    assert reopened == ["task-001", "task-002"]
    history = json.loads(
        (project / "evidence" / "remediation_history.json").read_text(encoding="utf-8")
    )
    assert history["events"][-1]["fallback_all_tasks"] is True


def test_unknown_retry_task_is_rejected(tmp_path: Path) -> None:
    project = _prepare_completed_assignments(tmp_path)

    with pytest.raises(ValueError, match="inconnues"):
        reopen_tasks_for_correction(
            project,
            {"verdict": "FAIL", "retry_task_ids": ["task-999"]},
            source="validation",
        )


def test_attempt_limit_requires_human_intervention(tmp_path: Path) -> None:
    project = _prepare_completed_assignments(tmp_path)
    record_task_result(
        project,
        "task-001",
        agent="ingenieur-devops",
        success=True,
        returncode=0,
        evidence_file="evidence/run-002.json",
        collected_outputs=[],
    )

    with pytest.raises(RuntimeError, match="intervention humaine"):
        reopen_tasks_for_correction(
            project,
            {"verdict": "FAIL", "retry_task_ids": ["task-001"]},
            source="validation",
        )


def test_pass_report_does_not_reopen_tasks(tmp_path: Path) -> None:
    project = _prepare_completed_assignments(tmp_path)

    assert (
        reopen_tasks_for_correction(
            project,
            {"verdict": "PASS", "retry_task_ids": []},
            source="validation",
        )
        == []
    )
    payload = _assignments(project)
    assert all(task["status"] == "PASS" for task in payload["tasks"])
