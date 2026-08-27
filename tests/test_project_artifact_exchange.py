from __future__ import annotations

import json
from pathlib import Path

from clawlocal.project_artifact_exchange import (
    affected_agents_after_publish,
    publish_task_outputs,
    validate_exchange_completeness,
    validate_exchange_for_task,
)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "platform" / "projects" / "projet-test"
    (project / "context").mkdir(parents=True)
    (project / "deliverables" / "tasks" / "task-a" / "architecte-solutions" / "run-001").mkdir(
        parents=True
    )
    (project / "context" / "project_plan.json").write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "task-a",
                        "role": "architecte-solutions",
                        "depends_on": [],
                    },
                    {
                        "id": "task-b",
                        "role": "ingenieur-devops",
                        "depends_on": ["task-a"],
                    },
                    {
                        "id": "task-c",
                        "role": "redacteur-technique",
                        "depends_on": ["task-b"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    output = (
        project
        / "deliverables"
        / "tasks"
        / "task-a"
        / "architecte-solutions"
        / "run-001"
        / "architecture.md"
    )
    output.write_text("# Architecture\n", encoding="utf-8")
    return project


def _write_assignments(project: Path, *, task_b_status: str = "PENDING") -> None:
    payload = {
        "tasks": [
            {"task_id": "task-a", "role": "architecte-solutions", "status": "PASS", "attempts": 1},
            {
                "task_id": "task-b",
                "role": "ingenieur-devops",
                "status": task_b_status,
                "attempts": 1 if task_b_status != "PENDING" else 0,
            },
            {"task_id": "task-c", "role": "redacteur-technique", "status": "PENDING", "attempts": 0},
        ]
    }
    (project / "context" / "task_assignments.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_passed_outputs_propagate_to_direct_and_transitive_dependents(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = "deliverables/tasks/task-a/architecte-solutions/run-001/architecture.md"

    bundles = publish_task_outputs(
        project,
        producer_task_id="task-a",
        agent="architecte-solutions",
        attempt=1,
        status="PASS",
        collected_outputs=[output],
    )

    assert "context/exchange/task-a/self/run-001" in bundles
    assert "context/exchange/task-b/dependencies/task-a/run-001" in bundles
    assert "context/exchange/task-c/dependencies/task-a/run-001" in bundles
    assert affected_agents_after_publish(project, "task-a", status="PASS") == [
        "architecte-solutions",
        "ingenieur-devops",
        "redacteur-technique",
    ]

    copied = (
        project
        / "context"
        / "exchange"
        / "task-b"
        / "dependencies"
        / "task-a"
        / "run-001"
        / "artifacts"
        / output
    )
    assert copied.read_text(encoding="utf-8") == "# Architecture\n"
    assert validate_exchange_for_task(project, "task-b") == []

    _write_assignments(project)
    assert validate_exchange_completeness(project) == []


def test_failed_attempt_is_preserved_only_as_self_history(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = "deliverables/tasks/task-a/architecte-solutions/run-001/architecture.md"
    publish_task_outputs(
        project,
        producer_task_id="task-a",
        agent="architecte-solutions",
        attempt=1,
        status="FAIL",
        collected_outputs=[output],
    )

    assert (project / "context/exchange/task-a/self/run-001/manifest.json").is_file()
    assert not (project / "context/exchange/task-b/dependencies/task-a/run-001").exists()
    assert affected_agents_after_publish(project, "task-a", status="FAIL") == [
        "architecte-solutions"
    ]


def test_exchange_hash_tampering_is_detected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = "deliverables/tasks/task-a/architecte-solutions/run-001/architecture.md"
    publish_task_outputs(
        project,
        producer_task_id="task-a",
        agent="architecte-solutions",
        attempt=1,
        status="PASS",
        collected_outputs=[output],
    )
    copied = (
        project
        / "context"
        / "exchange"
        / "task-b"
        / "dependencies"
        / "task-a"
        / "run-001"
        / "artifacts"
        / output
    )
    copied.write_text("tampered", encoding="utf-8")

    failures = validate_exchange_for_task(project, "task-b")
    assert any("modifié" in failure or "digest agrégé" in failure for failure in failures)


def test_exchange_completeness_fails_when_pass_bundle_is_missing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write_assignments(project)

    failures = validate_exchange_completeness(project)
    assert any("self-history absent" in failure for failure in failures)
