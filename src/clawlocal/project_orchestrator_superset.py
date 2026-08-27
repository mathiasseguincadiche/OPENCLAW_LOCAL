from __future__ import annotations

from pathlib import Path
from typing import Any

from clawlocal import project_orchestrator as base
from clawlocal.project_contracts import normalize_plan_payload, validate_project_manifest
from clawlocal.project_governance import (
    append_decision,
    append_risk,
    assert_transition_criticality_gates,
    record_criticality_gate,
    required_criticality_gates,
)
from clawlocal.project_integrity import snapshot_integrity

all_tasks_finished = base.all_tasks_finished
build_phase_prompt = base.build_phase_prompt
create_assignments = base.create_assignments
open_blocking_clarifications = base.open_blocking_clarifications
pending_tasks = base.pending_tasks
project_path = base.project_path
record_task_result = base.record_task_result
resolve_clarification = base.resolve_clarification
store_clarifications_from_analysis = base.store_clarifications_from_analysis
store_review_report = base.store_review_report
store_validation_report = base.store_validation_report


def load_project_manifest(project: Path) -> dict[str, Any]:
    return validate_project_manifest(base.load_project_manifest(project))


def current_status(project: Path) -> str:
    return str(load_project_manifest(project)["status"])


def store_analysis(project: Path, payload: dict[str, Any]) -> Path:
    path = base.store_analysis(project, payload)
    for value in payload.get("risks", []):
        text = str(value.get("description") if isinstance(value, dict) else value).strip()
        if text:
            append_risk(project, risk=text)
    for value in payload.get("decisions_required", []):
        text = str(value.get("description") if isinstance(value, dict) else value).strip()
        if text:
            append_decision(
                project,
                decision=f"Décision requise: {text}",
                rationale="Identifiée pendant l'analyse; résolution humaine ou planifiée requise.",
                actor="chef-operations",
            )
    return path


def store_plan(project: Path, payload: dict[str, Any]) -> Path:
    return base.store_plan(project, normalize_plan_payload(payload))


def _record_automatic_gate_evidence(
    project: Path,
    target: str,
    *,
    actor: str,
    human_approved: bool,
) -> None:
    required = required_criticality_gates(load_project_manifest(project))
    if target == "VALIDATING" and "evidence_required" in required:
        record_criticality_gate(
            project,
            "evidence_required",
            actor=actor,
            evidence="task_assignments: toutes les tâches sont PASS",
        )
    if target == "REVIEW" and "independent_audit_required" in required:
        record_criticality_gate(
            project,
            "independent_audit_required",
            actor=actor,
            evidence="validation.json: verdict PASS avant REVIEW",
        )
    if target == "COMPLETE" and "human_final_approval_required" in required:
        if human_approved:
            record_criticality_gate(
                project,
                "human_final_approval_required",
                actor="human",
                evidence="approbation humaine finale avant COMPLETE",
                human_approved=True,
            )


def transition_project(
    project: Path,
    target: str,
    *,
    actor: str,
    reason: str,
    human_approved: bool = False,
) -> dict[str, Any]:
    validate_project_manifest(base.load_project_manifest(project))
    base._assert_transition_gates(project, target, human_approved=human_approved)
    _record_automatic_gate_evidence(
        project,
        target,
        actor=actor,
        human_approved=human_approved,
    )
    assert_transition_criticality_gates(project, target)
    result = base.transition_project(
        project,
        target,
        actor=actor,
        reason=reason,
        human_approved=human_approved,
    )
    validate_project_manifest(result)
    if target in {"PLANNED", "VALIDATING", "REVIEW", "PACKAGING", "COMPLETE"}:
        snapshot_integrity(project, target)
    return result


def package_project(project: Path) -> tuple[Path, Path]:
    snapshot_integrity(project, "PRE_PACKAGE")
    archive, manifest = base.package_project(project)
    snapshot_integrity(
        project,
        "PACKAGE",
        roots=["project.json", "deliverables", "diagrams", "context"],
    )
    return archive, manifest
