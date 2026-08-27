from __future__ import annotations

import json
from pathlib import Path

import pytest

from clawlocal.project_ingestion import ingest_project_documents
from clawlocal.project_orchestrator_superset import (
    all_tasks_finished,
    build_phase_prompt,
    store_analysis,
)


def test_phase_prompts_require_ingestion_and_exchange() -> None:
    analyze = build_phase_prompt("projet-test", "analyze")
    execute = build_phase_prompt("projet-test", "execute", task_id="task-001")
    review = build_phase_prompt("projet-test", "review")

    assert "context/ingestion/index.json" in analyze
    assert "source_coverage" in analyze
    assert "outil pdf" in analyze
    assert "view_image" in analyze
    assert "context/exchange/task-001" in execute
    assert "lecture seule" in execute
    assert "context/exchange/" in review


def test_store_analysis_requires_complete_document_coverage(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "intake").mkdir(parents=True)
    (project / "context").mkdir()
    (project / "intake" / "brief.md").write_text("# Brief\n", encoding="utf-8")
    index = json.loads(ingest_project_documents(project).read_text(encoding="utf-8"))
    document_id = index["entries"][0]["document_id"]

    base_payload: dict[str, object] = {
        "summary": "Projet",
        "objectives": ["Livrer"],
        "constraints": [],
        "deliverables": ["README"],
        "ambiguities": [],
        "missing_information": [],
        "risks": [],
        "decisions_required": [],
    }
    with pytest.raises(ValueError, match="source_coverage"):
        store_analysis(project, dict(base_payload))

    payload = dict(base_payload)
    payload["source_coverage"] = [
        {
            "document_id": document_id,
            "status": "READ",
            "method": "local_text_extract",
            "notes": "brief lu",
        }
    ]
    path = store_analysis(project, payload)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["source_coverage"][0]["document_id"] == document_id


def test_all_tasks_finished_is_fail_closed_without_exchange(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "context").mkdir(parents=True)
    (project / "context" / "project_plan.json").write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "task-001",
                        "role": "ingenieur-devops",
                        "depends_on": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (project / "context" / "task_assignments.json").write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "task-001",
                        "role": "ingenieur-devops",
                        "depends_on": [],
                        "status": "PASS",
                        "attempts": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert all_tasks_finished(project) is False
