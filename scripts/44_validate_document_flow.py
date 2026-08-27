from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"


def load(name: str) -> dict[str, Any]:
    payload = yaml.safe_load((CONFIG / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return payload


def main() -> int:
    failures: list[str] = []
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    ingestion = load("document_ingestion_policy.yaml")
    exchange = load("artifact_exchange_policy.yaml")
    orchestration = load("orchestration_policy.yaml")
    tools = load("tool_policy.yaml")
    catalog = load("model_catalog.yaml")

    for name, contract in (
        ("document_ingestion_policy.yaml", ingestion),
        ("artifact_exchange_policy.yaml", exchange),
    ):
        if str(contract.get("platform_version")) != version:
            failures.append(f"{name}: platform_version incohérente")

    if ingestion.get("enabled") is not True or ingestion.get("local_first") is not True:
        failures.append("Document Ingestion doit rester activé et local-first")
    if ingestion.get("source_root") != "intake":
        failures.append("Document Ingestion doit partir de intake/")
    if ingestion.get("originals_immutable") is not True:
        failures.append("les originaux Intake doivent rester immuables")
    if ingestion.get("source_repository_is_not_replaced_by_extraction") is not True:
        failures.append("l'extraction ne doit jamais remplacer les sources de vérité")

    gate = ingestion.get("analysis_gate", {})
    for key in (
        "require_index_before_analysis",
        "require_complete_source_coverage",
        "unreadable_document_must_be_reported_as_missing_information",
        "stale_index_blocks_analysis",
    ):
        if gate.get(key) is not True:
            failures.append(f"Document Ingestion gate absent: {key}")

    formats = ingestion.get("formats", {})
    pdf = formats.get("pdf", {})
    image = formats.get("image", {})
    pdf_vision_fallback = pdf.get("supports_scanned_pages_via_vision_fallback")
    if pdf.get("tool") != "pdf" or pdf_vision_fallback is not True:
        failures.append("PDF: outil local/fallback vision incomplet")
    if int(pdf.get("max_pages_per_tool_call", 0)) < 1:
        failures.append("PDF: max_pages_per_tool_call invalide")
    if pdf.get("chunk_large_documents") is not True:
        failures.append("PDF: les gros documents doivent être traités par tranches")
    if image.get("tool") != "view_image":
        failures.append("images: view_image requis")
    for kind in ("office_text", "office_slides", "office_sheet"):
        if formats.get(kind, {}).get("method") != "local_zip_xml_extract":
            failures.append(f"{kind}: extraction locale déterministe requise")
    if ingestion.get("security", {}).get("cloud_for_document_ingestion") is not False:
        failures.append("Document Ingestion ne doit pas nécessiter le cloud")

    if exchange.get("enabled") is not True:
        failures.append("Artifact Exchange doit rester activé")
    principles = exchange.get("principles", {})
    for key in (
        "central_project_is_source_of_truth",
        "agent_workspaces_are_disposable_snapshots",
        "never_overwrite_previous_runs",
        "publish_self_history_for_every_attempt",
        "publish_to_dependents_only_on_pass",
        "preserve_provenance",
        "hash_every_exchanged_file",
        "consumer_must_not_modify_exchange_in_place",
    ):
        if principles.get(key) is not True:
            failures.append(f"Artifact Exchange principle absent: {key}")
    propagation = exchange.get("propagation", {})
    for key in (
        "direct_dependents",
        "transitive_dependents",
        "resync_consumer_before_each_task",
        "include_previous_self_attempts",
    ):
        if propagation.get(key) is not True:
            failures.append(f"Artifact Exchange propagation absente: {key}")

    engine = orchestration.get("engine", {})
    if engine.get("document_ingestion_required_before_analysis") is not True:
        failures.append("orchestrateur: ingestion obligatoire avant analyse")
    if engine.get("artifact_exchange_fail_closed") is not True:
        failures.append("orchestrateur: Artifact Exchange doit rester fail-closed")
    execution = orchestration.get("execution", {})
    for key in (
        "propagate_passed_outputs_to_dependents",
        "resync_affected_agents_after_task",
        "preserve_self_attempt_history",
    ):
        if execution.get(key) is not True:
            failures.append(f"orchestrateur document flow absent: {key}")

    expected_roles = set(tools.get("agents", {}))
    if len(expected_roles) != 8:
        failures.append("tool_policy: huit agents requis")
    for role, entry in tools.get("agents", {}).items():
        allowed = set(entry.get("also_allow", []))
        if not {"pdf", "view_image"} <= allowed:
            failures.append(f"{role}: pdf/view_image doivent être explicitement autorisés")

    for alias in ("qwen-max", "gemma-deep", "devstral-devops"):
        model = catalog.get("models", {}).get(alias, {})
        if "image" not in model.get("input", []):
            failures.append(f"{alias}: entrée image requise pour le parcours documentaire")

    required_files = (
        "src/clawlocal/project_ingestion.py",
        "src/clawlocal/project_artifact_exchange.py",
        "scripts/42_project_ingest.py",
        "scripts/43_project_exchange.py",
        "docs/DOCUMENT_INGESTION_AND_EXCHANGE.md",
    )
    for relative in required_files:
        if not (ROOT / relative).is_file():
            failures.append(f"fichier document flow absent: {relative}")

    openclaw_source = (ROOT / "src/clawlocal/openclaw_config.py").read_text(encoding="utf-8")
    for marker in ("imageModel", "pdfModel", "pdfMaxPages", "document_ingestion_policy.yaml"):
        if marker not in openclaw_source:
            failures.append(f"OpenClaw document config non câblée: {marker}")

    migration_source = (ROOT / "src/clawlocal/project_migrations.py").read_text(encoding="utf-8")
    for marker in ("ingest_project_documents", "validate_ingestion_index"):
        if marker not in migration_source:
            failures.append(f"projets existants non bootstrapés pour ingestion: {marker}")

    orchestrator_source = (
        ROOT / "src/clawlocal/project_orchestrator_superset.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "validate_source_coverage",
        "publish_task_outputs",
        "validate_exchange_completeness",
        "affected_agents_after_publish",
        "sync_project_context",
        "context/exchange",
        "context/ingestion",
    ):
        if marker not in orchestrator_source:
            failures.append(f"orchestrateur document flow non câblé: {marker}")

    ingestion_source = (ROOT / "src/clawlocal/project_ingestion.py").read_text(encoding="utf-8")
    for marker in (
        "validate_source_coverage",
        "validate_ingestion_index",
        "local_zip_xml_extract",
        "READY_TOOL",
    ):
        if marker not in ingestion_source:
            failures.append(f"ingestion exécutable incomplète: {marker}")

    exchange_source = (
        ROOT / "src/clawlocal/project_artifact_exchange.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "publish_task_outputs",
        "validate_exchange_completeness",
        "aggregate_sha256",
        "transitive_dependents",
    ):
        if marker not in exchange_source:
            failures.append(f"Artifact Exchange exécutable incomplet: {marker}")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2
    print("OK  Document Ingestion + Artifact Exchange Gate")
    print("OK  PDF/images local-first + Office/text deterministic extraction")
    print("OK  source_coverage complet et ingestion stale fail-closed")
    print("OK  artefacts versionnés, hashés, propagés et resynchronisés")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
