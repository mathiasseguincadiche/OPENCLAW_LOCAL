from __future__ import annotations

from pathlib import Path
from typing import Any

from clawlocal import project_orchestrator as base
from clawlocal.project_artifact_exchange import (
    affected_agents_after_publish,
    publish_task_outputs,
    validate_exchange_completeness,
    validate_exchange_for_task,
)
from clawlocal.project_context import sync_project_context
from clawlocal.project_contracts import normalize_plan_payload, validate_project_manifest
from clawlocal.project_governance import (
    append_decision,
    append_risk,
    assert_transition_criticality_gates,
    record_criticality_gate,
    required_criticality_gates,
)
from clawlocal.project_ingestion import ingest_project_documents, validate_ingestion_index
from clawlocal.project_ingestion_pre_v1 import (
    ensure_secure_generic_zip_ingestion,
    validate_source_coverage_pre_v1,
)
from clawlocal.project_integrity import snapshot_integrity
from clawlocal.project_traceability import (
    normalize_analysis_requirements,
    refresh_traceability_matrix,
    traceability_failures,
    validate_plan_requirement_links,
)
from clawlocal.project_web_evidence import (
    project_web_evidence_failures,
    task_web_evidence_failures,
)
from clawlocal.safe_fs import assert_no_link_like

create_assignments = base.create_assignments
open_blocking_clarifications = base.open_blocking_clarifications
project_path = base.project_path
resolve_clarification = base.resolve_clarification
store_clarifications_from_analysis = base.store_clarifications_from_analysis


def load_project_manifest(project: Path) -> dict[str, Any]:
    return validate_project_manifest(base.load_project_manifest(project))


def current_status(project: Path) -> str:
    return str(load_project_manifest(project)["status"])


def _pedagogy_phase_context(phase: str) -> str:
    context = (
        " Applique le contrat pédagogique transversal du workspace. Lis "
        "context/learning/LEARNING_CONTRACT.json, context/learning/learning_profile.json et "
        "context/documentation_profile.json lorsqu'ils existent. Pour les champs textuels et "
        "tout artefact destiné à un humain, reste techniquement exact, précis et accessible à un "
        "débutant sans fausse simplification ni ton infantilisant; conserve la profondeur expert "
        "utile. Explicite proportionnellement but, vocabulaire, prérequis, résultat attendu, "
        "validation, risques, limites et rollback. Utilise les profondeurs Comprendre, Utiliser, "
        "Approfondir et Diagnostiquer lorsque cela améliore réellement la compréhension."
    )
    if phase in {"validate", "review"}:
        context += (
            " Audite aussi la qualité pédagogique et l'accessibilité: objectif compréhensible, "
            "prérequis explicites, jargon défini, étapes actionnables, résultat et validation "
            "visibles, risques/rollback présents quand nécessaires, profondeur expert préservée. "
            "Un livrable techniquement correct mais inutilisable ou trompeusement simplifié doit "
            "être signalé comme finding."
        )
    return context


def _web_verification_context(phase: str, task_id: str | None = None) -> str:
    if phase == "analyze":
        return (
            " Identifie explicitement les faits externes susceptibles d'avoir changé: versions, "
            "releases, compatibilités, vulnérabilités, règles, état d'un service ou documentation "
            "courante. Ne transforme jamais l'âge de publication d'une page en preuve que le fait "
            "est encore actuel: la currentness doit être vérifiée au moment de la recherche."
        )
    if phase == "plan":
        return (
            " Pour chaque tâche qui doit établir un fait Web actuel ou volatil, ajoute "
            "web_evidence dans required_evidence. Si une affirmation technique peut être "
            "vérifiée sur le runtime, le schéma, la CLI, une API, un dry-run, un test ou un "
            "registre, ajoute aussi runtime_evidence. Ces marqueurs sont des gates bloquants."
        )
    if phase == "execute" and task_id is not None:
        return (
            f" Si context/tasks/{task_id}.json exige web_evidence, produis exactement "
            f"evidence/{task_id}/web_evidence.json selon config/v1/web_policy.yaml. Enregistre "
            "published_at/updated_at quand la source les expose, toujours retrieved_at, son niveau "
            "d'autorité, les affirmations supportées, la currentness, les contradictions et le "
            "niveau de confiance. Pour toute affirmation machine_verifiable, joins une preuve "
            "runtime PASS récente. Une contradiction ouverte ou une affirmation non vérifiée ne "
            "doit jamais être masquée par une synthèse affirmative."
        )
    if phase in {"validate", "review"}:
        return (
            " Audite aussi les required_evidence des tâches. Toute tâche exigeant web_evidence "
            "doit posséder un web_evidence.json valide: source autoritative actuelle pour les "
            "faits volatils, corroboration suffisante, éditeurs distincts lorsque requis, aucune "
            "contradiction ouverte, confiance minimale respectée et preuve runtime pour les faits "
            "machine_verifiable. Si un fait externe actuel est utilisé sans avoir été classé comme "
            "nécessitant web_evidence, signale cette omission comme finding bloquant."
        )
    return ""


def _traceability_context(phase: str) -> str:
    if phase == "analyze":
        return (
            " Produis aussi requirements[]: une exigence atomique et vérifiable par entrée, avec "
            "{id,statement,type,priority,source_document_ids[],source_refs[],acceptance_hint}. "
            "Utilise des identifiants stables REQ-001, REQ-002, etc. source_document_ids doit "
            "référencer les document_id de context/ingestion/index.json; source_refs peut pointer "
            "vers une section, page, chemin source ou décision humaine. Ne fusionne pas deux "
            "exigences indépendantes sous un même REQ."
        )
    if phase == "plan":
        return (
            " Chaque tâche doit contenir requirement_ids[] avec les REQ qu'elle contribue à "
            "satisfaire. Toutes les exigences explicites doivent être couvertes par au moins une "
            "tâche; une tâche purement support peut avoir requirement_ids vide. Les "
            "acceptance_criteria et required_evidence doivent rendre cette couverture vérifiable."
        )
    if phase in {"validate", "review"}:
        return (
            " Consulte context/traceability/requirements_matrix.json et audite la chaîne "
            "REQ -> tâche -> sortie observée -> preuve -> verdict. Une exigence non mappée, sans "
            "preuve observable ou dont une tâche est en échec est bloquante."
        )
    return ""


def build_phase_prompt(project_id: str, phase: str, *, task_id: str | None = None) -> str:
    prompt = base.build_phase_prompt(project_id, phase, task_id=task_id)
    prompt += _pedagogy_phase_context(phase)
    prompt += _web_verification_context(phase, task_id)
    prompt += _traceability_context(phase)
    if phase == "analyze":
        return prompt + (
            " Lis aussi context/ingestion/index.json avant de conclure. Pour chaque document "
            "indexé, utilise derived_path quand status=READY_TEXT/PARTIAL_TEXT; utilise l'outil "
            "pdf sur source_path pour un PDF et view_image pour une image. Pour kind=zip avec "
            "status=READY_ARCHIVE, lis archive.md et archive_manifest.json puis inspecte les "
            "membres dérivés pertinents; les archives imbriquées restent opaques. Utilise pdf ou "
            "view_image sur un membre dérivé si son type l'exige. Un PDF long doit être parcouru "
            "par tranches jusqu'à couvrir le document utile. Ajoute source_coverage[] avec "
            "exactement une entrée par document: {document_id,status,method,notes}; status vaut "
            "READ, PARTIAL ou UNREADABLE, et method vaut local_text_extract, "
            "local_zip_xml_extract, local_safe_archive_extract, pdf, view_image ou raw_file. "
            "Tout UNREADABLE doit aussi être expliqué dans missing_information[]."
        )
    if phase == "plan":
        return prompt + (
            " Utilise context/ingestion/index.json, source_coverage et requirements de "
            "project_analysis.json. Une source PARTIAL/UNREADABLE ne peut pas être silencieusement "
            "considérée comme lue."
        )
    if phase == "execute" and task_id is not None:
        return prompt + (
            f" Consulte aussi context/exchange/{task_id}/ si ce dossier existe: dependencies/ "
            "contient les sorties validées des tâches amont et self/ contient les tentatives "
            "précédentes de cette tâche. Ces artefacts sont des entrées versionnées en lecture "
            "seule; ne les modifie pas en place. Produis une nouvelle sortie dans les répertoires "
            "de la tâche."
        )
    if phase in {"validate", "review"}:
        return prompt + (
            " Vérifie aussi context/ingestion/index.json et source_coverage dans "
            "project_analysis.json, ainsi que les manifests sous context/exchange/. Un document "
            "déclaré non couvert ou un échange d'artefact incohérent est un finding bloquant, pas "
            "une hypothèse à combler."
        )
    return prompt


def store_analysis(project: Path, payload: dict[str, Any]) -> Path:
    ingestion_index = project / "context" / "ingestion" / "index.json"
    if not ingestion_index.is_file():
        ingest_project_documents(project)
    ensure_secure_generic_zip_ingestion(project)
    validate_ingestion_index(project)
    coverage = payload.get("source_coverage", [])
    missing_information = payload.get("missing_information", [])
    if not isinstance(coverage, list):
        raise ValueError("analyse: source_coverage doit être une liste")
    if not isinstance(missing_information, list):
        raise ValueError("analyse: missing_information doit être une liste")
    normalized = dict(payload)
    normalized["source_coverage"] = validate_source_coverage_pre_v1(
        project, coverage, missing_information
    )
    normalized = normalize_analysis_requirements(project, normalized)
    path = base.store_analysis(project, normalized)
    for value in normalized.get("risks", []):
        text = str(value.get("description") if isinstance(value, dict) else value).strip()
        if text:
            append_risk(project, risk=text)
    for value in normalized.get("decisions_required", []):
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
    normalized = normalize_plan_payload(payload)
    validate_plan_requirement_links(project, normalized)
    path = base.store_plan(project, normalized)
    refresh_traceability_matrix(project)
    return path


def pending_tasks(project: Path) -> list[dict[str, Any]]:
    ready = base.pending_tasks(project)
    for task in ready:
        task_id = str(task.get("task_id", ""))
        failures = validate_exchange_for_task(project, task_id)
        if failures:
            raise ValueError(
                f"artifact exchange invalide pour {task_id}: " + "; ".join(failures)
            )
    return ready


def all_tasks_finished(project: Path) -> bool:
    if not base.all_tasks_finished(project):
        return False
    return not validate_exchange_completeness(project)


def record_task_result(
    project: Path,
    task_id: str,
    *,
    agent: str,
    success: bool,
    returncode: int,
    evidence_file: str,
    collected_outputs: list[str],
) -> dict[str, Any]:
    if success:
        web_failures = task_web_evidence_failures(project, task_id)
        if web_failures:
            raise ValueError(
                f"tâche {task_id}: preuves Web invalides: " + "; ".join(web_failures)
            )
    assignment = base.record_task_result(
        project,
        task_id,
        agent=agent,
        success=success,
        returncode=returncode,
        evidence_file=evidence_file,
        collected_outputs=collected_outputs,
    )
    attempt = int(assignment["attempts"])
    status = str(assignment["status"])
    publish_task_outputs(
        project,
        producer_task_id=task_id,
        agent=agent,
        attempt=attempt,
        status=status,
        collected_outputs=collected_outputs,
    )
    refresh_traceability_matrix(project)

    platform_root = project.resolve().parents[1]
    if (platform_root / "workspaces").is_dir():
        for affected_agent in affected_agents_after_publish(project, task_id, status=status):
            sync_project_context(
                platform_root,
                project.name,
                affected_agent,
                include_outputs=False,
            )
    return assignment


def store_validation_report(project: Path, payload: dict[str, Any]) -> Path:
    path = base.store_validation_report(project, payload)
    refresh_traceability_matrix(project)
    return path


def store_review_report(project: Path, payload: dict[str, Any]) -> Path:
    path = base.store_review_report(project, payload)
    refresh_traceability_matrix(project)
    return path


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
    if target == "COMPLETE" and "human_final_approval_required" in required and human_approved:
        record_criticality_gate(
            project,
            "human_final_approval_required",
            actor="human",
            evidence="approbation humaine finale avant COMPLETE",
            human_approved=True,
        )


def _assert_pre_v1_gates(project: Path, target: str) -> None:
    if target not in {"VALIDATING", "REVIEW", "PACKAGING", "COMPLETE"}:
        return
    failures = validate_exchange_completeness(project)
    if failures:
        raise PermissionError(
            f"transition vers {target} bloquée; artifact exchange incomplet: "
            + "; ".join(failures)
        )
    web_failures = project_web_evidence_failures(project)
    if web_failures:
        raise PermissionError(
            f"transition vers {target} bloquée; preuves Web invalides: "
            + "; ".join(web_failures)
        )
    trace_failures = traceability_failures(project, require_completed=True)
    if trace_failures:
        raise PermissionError(
            f"transition vers {target} bloquée; traçabilité exigences incomplète: "
            + "; ".join(trace_failures)
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
    _assert_pre_v1_gates(project, target)
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
    _assert_pre_v1_gates(project, "PACKAGING")
    for name in ("deliverables", "diagrams", "context"):
        root = project / name
        if root.exists():
            assert_no_link_like(root, label=f"packaging {name}")
    snapshot_integrity(project, "PRE_PACKAGE")
    archive, manifest = base.package_project(project)
    snapshot_integrity(
        project,
        "PACKAGE",
        roots=["project.json", "deliverables", "diagrams", "context"],
    )
    return archive, manifest
