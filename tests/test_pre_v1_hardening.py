from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from clawlocal import model_identity
from clawlocal.golden_projects import evaluate_golden_project, prepare_golden_project
from clawlocal.project_ingestion import ingest_project_documents, load_ingestion_index
from clawlocal.project_ingestion_pre_v1 import (
    ensure_secure_generic_zip_ingestion,
    validate_source_coverage_pre_v1,
)
from clawlocal.project_traceability import (
    normalize_analysis_requirements,
    refresh_traceability_matrix,
    validate_plan_requirement_links,
)
from clawlocal.safe_archive import safe_extract_zip
from clawlocal.workspace_guard import (
    allowed_output_kinds,
    validate_workspace_guard,
    write_workspace_guard,
)


def test_safe_zip_extracts_hashes_and_keeps_nested_archive_opaque(tmp_path: Path) -> None:
    source = tmp_path / "project.zip"
    nested_bytes = b"PK\x03\x04opaque-nested-archive"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("src/main.py", "print('ok')\n")
        archive.writestr("assets/nested.zip", nested_bytes)
    target = tmp_path / "derived"
    members = safe_extract_zip(
        source,
        target,
        {
            "max_archive_bytes_mb": 10,
            "max_members": 20,
            "max_total_uncompressed_mb": 20,
            "max_single_member_mb": 10,
            "max_compression_ratio": 200,
            "max_depth": 8,
            "reject_encrypted_members": True,
        },
    )
    by_path = {str(item["member_path"]): item for item in members}
    assert (target / "src" / "main.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert by_path["src/main.py"]["sha256"]
    assert by_path["assets/nested.zip"]["nested_archive"] is True
    assert (target / "assets" / "nested.zip").read_bytes() == nested_bytes
    assert not (target / "assets" / "nested").exists()


def test_safe_zip_rejects_zip_slip(tmp_path: Path) -> None:
    source = tmp_path / "escape.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("../escape.txt", "no")
    with pytest.raises(ValueError, match="chemin dangereux"):
        safe_extract_zip(
            source,
            tmp_path / "out",
            {
                "max_archive_bytes_mb": 10,
                "max_members": 20,
                "max_total_uncompressed_mb": 20,
                "max_single_member_mb": 10,
                "max_compression_ratio": 200,
                "max_depth": 8,
                "reject_encrypted_members": True,
            },
        )
    assert not (tmp_path / "escape.txt").exists()


def test_generic_zip_bridge_updates_ingestion_and_coverage(tmp_path: Path) -> None:
    project = tmp_path / "project"
    intake = project / "intake"
    intake.mkdir(parents=True)
    with zipfile.ZipFile(intake / "client.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", "# Client\n")
        archive.writestr("infra/main.tf", 'resource "null_resource" "x" {}\n')
    ingest_project_documents(project)
    ensure_secure_generic_zip_ingestion(project)
    index = load_ingestion_index(project)
    entry = index["entries"][0]
    assert entry["kind"] == "zip"
    assert entry["status"] == "READY_ARCHIVE"
    assert entry["method"] == "local_safe_archive_extract"
    manifest = project / entry["archive_manifest_path"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["member_count"] == 2
    assert payload["nested_archives_recursive"] is False
    normalized = validate_source_coverage_pre_v1(
        project,
        [
            {
                "document_id": entry["document_id"],
                "status": "READ",
                "method": "local_safe_archive_extract",
                "notes": "archive inspectée",
            }
        ],
        [],
    )
    assert normalized[0]["method"] == "local_safe_archive_extract"


def test_workspace_guard_blocks_protected_input_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "intake").mkdir(parents=True)
    (workspace / "sources").mkdir()
    (workspace / "context" / "exchange").mkdir(parents=True)
    (workspace / "intake" / "brief.txt").write_text("original", encoding="utf-8")
    write_workspace_guard(workspace, "redacteur-technique")
    validate_workspace_guard(workspace, "redacteur-technique")
    (workspace / "intake" / "brief.txt").write_text("altéré", encoding="utf-8")
    with pytest.raises(PermissionError, match="entrée protégée modifiée"):
        validate_workspace_guard(workspace, "redacteur-technique")


def test_role_output_scopes_are_code_enforced() -> None:
    assert set(allowed_output_kinds("ingenieur-release-forges")) == {
        "work",
        "deliverables",
        "evidence",
    }
    assert set(allowed_output_kinds("redacteur-technique")) == {
        "work",
        "deliverables",
        "evidence",
        "diagrams",
    }
    assert set(allowed_output_kinds("auditeur-qualite")) == {"work", "evidence"}


def test_explicit_requirements_map_to_tasks_and_matrix(tmp_path: Path) -> None:
    project = tmp_path / "project"
    intake = project / "intake"
    intake.mkdir(parents=True)
    (intake / "brief.md").write_text("Le service doit exposer /health.\n", encoding="utf-8")
    ingest_project_documents(project)
    index = load_ingestion_index(project)
    document_id = str(index["entries"][0]["document_id"])
    analysis = normalize_analysis_requirements(
        project,
        {
            "summary": "test",
            "objectives": ["exposer health"],
            "constraints": [],
            "deliverables": ["service"],
            "ambiguities": [],
            "missing_information": [],
            "risks": [],
            "decisions_required": [],
            "source_coverage": [],
            "requirements": [
                {
                    "id": "REQ-001",
                    "statement": "Le service expose /health.",
                    "type": "functional",
                    "priority": "must",
                    "source_document_ids": [document_id],
                    "source_refs": ["brief.md:1"],
                    "acceptance_hint": "HTTP 200",
                }
            ],
        },
    )
    (project / "context").mkdir(exist_ok=True)
    (project / "context" / "project_analysis.json").write_text(
        json.dumps(analysis), encoding="utf-8"
    )
    plan = {
        "workstreams": ["service"],
        "tasks": [
            {
                "id": "task-health",
                "role": "ingenieur-devops",
                "title": "Health endpoint",
                "objective": "fournir le contrôle de santé",
                "requirement_ids": ["REQ-001"],
                "expected_outputs": ["deliverables/health.txt"],
                "acceptance_criteria": ["/health retourne 200"],
            }
        ],
    }
    validate_plan_requirement_links(project, plan)
    (project / "context" / "project_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    matrix_path = refresh_traceability_matrix(project)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["requirements_origin"] == "explicit"
    assert matrix["rows"][0]["requirement_id"] == "REQ-001"
    assert matrix["rows"][0]["tasks"] == ["task-health"]
    assert matrix["rows"][0]["verdict"] == "PENDING"


def test_explicit_requirement_cannot_be_left_unmapped(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "context").mkdir(parents=True)
    (project / "context" / "project_analysis.json").write_text(
        json.dumps(
            {
                "requirements_origin": "explicit",
                "requirements": [{"id": "REQ-001", "statement": "x"}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exigences non affectées"):
        validate_plan_requirement_links(
            project,
            {
                "tasks": [
                    {
                        "id": "task-support",
                        "role": "ingenieur-devops",
                        "requirement_ids": [],
                    }
                ]
            },
        )


def test_model_identity_change_invalidates_qualification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = {
        "schema_version": "1.0.0",
        "captured_at": "2026-01-01T00:00:00+00:00",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "models": {"qwen-max": {"runtime_id": "qwen", "digest": "aaa", "quantization_level": "Q4"}},
        "fingerprint_sha256": "fingerprint-a",
    }
    second = {
        **first,
        "captured_at": "2026-01-02T00:00:00+00:00",
        "models": {"qwen-max": {"runtime_id": "qwen", "digest": "bbb", "quantization_level": "Q5"}},
        "fingerprint_sha256": "fingerprint-b",
    }
    monkeypatch.setattr(model_identity, "current_model_identity", lambda: first)
    model_identity.capture_candidate(tmp_path)
    model_identity.promote_candidate(tmp_path)
    assert model_identity.check_qualified(tmp_path) == "QUALIFIED"
    monkeypatch.setattr(model_identity, "current_model_identity", lambda: second)
    assert model_identity.check_qualified(tmp_path) == "INVALIDATED"
    qualified = json.loads(
        (tmp_path / "state" / "qualification" / "qualified_model_identity.json").read_text(
            encoding="utf-8"
        )
    )
    assert qualified["status"] == "INVALIDATED"
    assert qualified["invalidation_reason"] == "runtime_model_identity_changed"


def test_prompt_injection_golden_fixture_is_real_document(tmp_path: Path) -> None:
    project = prepare_golden_project(tmp_path, "prompt-injection-document")
    index = load_ingestion_index(project)
    assert {entry["kind"] for entry in index["entries"]} == {"docx"}
    derived = project / index["entries"][0]["derived_path"]
    assert "PROMPT_INJECTION_SUCCEEDED" in derived.read_text(encoding="utf-8")
    assert evaluate_golden_project(project, "prompt-injection-document") == []
