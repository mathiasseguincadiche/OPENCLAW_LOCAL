from pathlib import Path

import pytest

from clawlocal.project_context import collect_agent_outputs, sync_project_context
from clawlocal.project_intake import create_project
from clawlocal.project_orchestrator import (
    create_assignments,
    current_status,
    package_project,
    project_path,
    record_task_result,
    resolve_clarification,
    store_analysis,
    store_clarifications_from_analysis,
    store_plan,
    store_review_report,
    store_validation_report,
    transition_project,
)


def _analysis(*, ambiguity: bool = False) -> dict[str, object]:
    return {
        "summary": "Projet DevOps",
        "objectives": ["Produire un livrable vérifié"],
        "constraints": ["Local-first"],
        "deliverables": ["README"],
        "ambiguities": ["Choisir la cible"] if ambiguity else [],
        "missing_information": [],
        "risks": ["Erreur de configuration"],
        "decisions_required": [],
    }


def _plan() -> dict[str, object]:
    return {
        "workstreams": ["delivery"],
        "tasks": [
            {
                "id": "task-001",
                "title": "Produire le README",
                "role": "redacteur-technique",
                "objective": "Documenter le projet",
                "depends_on": [],
                "expected_outputs": ["README.md"],
                "acceptance_criteria": ["README non vide"],
                "needs_web": False,
                "security_sensitive": False,
            }
        ],
    }


def test_orchestration_stops_for_blocking_clarification(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    project = create_project(root, "projet-test", "Projet")
    store_analysis(project, _analysis(ambiguity=True))
    store_clarifications_from_analysis(project)

    transition_project(
        project,
        "ANALYZED",
        actor="chef-operations",
        reason="analysis_done",
    )
    transition_project(
        project,
        "CLARIFICATION_REQUIRED",
        actor="chef-operations",
        reason="blocking_question",
    )
    assert current_status(project) == "CLARIFICATION_REQUIRED"

    resolve_clarification(
        project,
        "clarification-001",
        "Utiliser Docker local.",
    )
    assert current_status(project) == "ANALYZED"


def test_plan_rejects_unknown_agent(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    project = create_project(root, "projet-test", "Projet")
    payload = _plan()
    tasks = payload["tasks"]
    assert isinstance(tasks, list)
    task = tasks[0]
    assert isinstance(task, dict)
    task["role"] = "agent-inconnu"

    with pytest.raises(ValueError, match="rôle inconnu"):
        store_plan(project, payload)


def test_full_state_machine_requires_human_completion(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    project = create_project(root, "projet-test", "Projet")

    store_analysis(project, _analysis())
    store_clarifications_from_analysis(project)
    transition_project(
        project,
        "ANALYZED",
        actor="chef-operations",
        reason="analysis_done",
    )

    store_plan(project, _plan())
    transition_project(
        project,
        "PLANNED",
        actor="chef-operations",
        reason="plan_done",
    )
    create_assignments(project)
    transition_project(
        project,
        "ASSIGNED",
        actor="chef-operations",
        reason="assigned",
    )
    transition_project(
        project,
        "IN_PROGRESS",
        actor="chef-operations",
        reason="execution_started",
    )

    record_task_result(
        project,
        "task-001",
        agent="redacteur-technique",
        success=True,
        returncode=0,
        evidence_file="evidence/run.json",
        collected_outputs=[],
    )
    transition_project(
        project,
        "VALIDATING",
        actor="chef-operations",
        reason="tasks_passed",
    )

    store_validation_report(
        project,
        {
            "verdict": "PASS",
            "findings": [],
            "task_results_summary": "OK",
            "recommendations": [],
        },
    )
    transition_project(
        project,
        "REVIEW",
        actor="auditeur-qualite",
        reason="validation_passed",
    )

    store_review_report(
        project,
        {
            "verdict": "PASS",
            "coverage": "100%",
            "missing_deliverables": [],
            "blocking_findings": [],
            "recommendations": [],
        },
    )
    transition_project(
        project,
        "PACKAGING",
        actor="auditeur-qualite",
        reason="review_passed",
    )

    deliverable = project / "deliverables" / "README.md"
    deliverable.write_text("# Projet\n", encoding="utf-8")
    archive, manifest = package_project(project)
    assert archive.is_file()
    assert manifest.is_file()

    with pytest.raises(PermissionError):
        transition_project(
            project,
            "COMPLETE",
            actor="human",
            reason="no_approval",
        )

    transition_project(
        project,
        "COMPLETE",
        actor="human",
        reason="approved",
        human_approved=True,
    )
    assert current_status(project) == "COMPLETE"


def test_collect_agent_outputs_namespaces_task_runs(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    create_project(root, "projet-test", "Projet")
    snapshot = sync_project_context(root, "projet-test", "ingenieur-devops")
    output = snapshot / "deliverables" / "task-001" / "main.tf"
    output.parent.mkdir(parents=True)
    output.write_text("terraform {}\n", encoding="utf-8")

    first = collect_agent_outputs(
        root,
        "projet-test",
        "ingenieur-devops",
        "task-001",
    )
    second = collect_agent_outputs(
        root,
        "projet-test",
        "ingenieur-devops",
        "task-001",
    )

    assert first == [
        "deliverables/tasks/task-001/ingenieur-devops/run-001/main.tf"
    ]
    assert second == [
        "deliverables/tasks/task-001/ingenieur-devops/run-002/main.tf"
    ]
    project = project_path(root, "projet-test")
    assert (project / first[0]).is_file()


def test_review_snapshot_can_include_central_outputs(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    project = create_project(root, "projet-test", "Projet")
    output = project / "deliverables" / "result.txt"
    output.write_text("preuve", encoding="utf-8")

    snapshot = sync_project_context(
        root,
        "projet-test",
        "auditeur-qualite",
        include_outputs=True,
    )

    assert (snapshot / "deliverables" / "result.txt").read_text(
        encoding="utf-8"
    ) == "preuve"
