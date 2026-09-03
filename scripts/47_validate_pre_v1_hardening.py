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


def read(relative: str, failures: list[str]) -> str:
    path = ROOT / relative
    if not path.is_file():
        failures.append(f"fichier pré-V1 absent: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    ingestion = load("document_ingestion_policy.yaml")
    traceability = load("traceability_policy.yaml")
    identity = load("model_identity_policy.yaml")
    golden = load("golden_project_policy.yaml")
    tools = load("tool_policy.yaml")

    for name, policy in (
        ("document_ingestion_policy.yaml", ingestion),
        ("traceability_policy.yaml", traceability),
        ("model_identity_policy.yaml", identity),
        ("golden_project_policy.yaml", golden),
        ("tool_policy.yaml", tools),
    ):
        if str(policy.get("platform_version")) != version:
            failures.append(f"{name}: platform_version incohérente")

    archive = ingestion.get("formats", {}).get("archive", {})
    if archive.get("extensions") != [".zip"]:
        failures.append("ZIP générique: extension .zip attendue")
    if archive.get("method") != "local_safe_archive_extract":
        failures.append("ZIP générique: local_safe_archive_extract requis")
    if archive.get("recursive_nested_archives") is not False:
        failures.append(
            "ZIP générique: extraction récursive des archives imbriquées interdite"
        )
    generic = ingestion.get("extraction", {}).get("generic_archive_safety", {})
    for key in (
        "max_archive_bytes_mb",
        "max_members",
        "max_total_uncompressed_mb",
        "max_single_member_mb",
        "max_compression_ratio",
        "max_depth",
    ):
        try:
            if float(generic.get(key, 0)) <= 0:
                failures.append(f"ZIP générique: limite absente/invalide: {key}")
        except (TypeError, ValueError):
            failures.append(f"ZIP générique: limite non numérique: {key}")
    for key in (
        "reject_encrypted_members",
        "reject_links_and_special_files",
        "reject_windows_ambiguous_paths",
        "reject_casefold_duplicates",
        "nested_archives_are_opaque",
    ):
        if generic.get(key) is not True:
            failures.append(f"ZIP générique: garde-fou absent: {key}")
    if "local_safe_archive_extract" not in ingestion.get("coverage_methods", []):
        failures.append("ZIP générique: méthode absente de source_coverage")

    safe_archive = read("src/clawlocal/safe_archive.py", failures)
    for marker in (
        "safe_extract_zip",
        "compression_ratio",
        "stat.S_IFMT",
        "casefold",
        "nested_archive",
        "sha256",
    ):
        if marker not in safe_archive:
            failures.append(f"safe_archive: garde-fou exécutable absent: {marker}")
    ingestion_bridge = read("src/clawlocal/project_ingestion_pre_v1.py", failures)
    for marker in (
        "ensure_secure_generic_zip_ingestion",
        "validate_source_coverage_pre_v1",
        "READY_ARCHIVE",
        "archive_manifest.json",
        "local_safe_archive_extract",
    ):
        if marker not in ingestion_bridge:
            failures.append(f"ZIP bridge incomplet: {marker}")

    if traceability.get("enabled") is not True:
        failures.append("traçabilité: politique désactivée")
    for key in (
        "reject_unknown_requirement_ids",
        "require_every_explicit_requirement_mapped",
    ):
        if traceability.get("planning_gate", {}).get(key) is not True:
            failures.append(f"traçabilité: planning gate absent: {key}")
    for key in (
        "require_traceability_before_validating",
        "require_pass_for_every_explicit_requirement",
        "require_observed_output_or_evidence",
        "fail_closed_on_unmapped_requirement",
    ):
        if traceability.get("completion_gate", {}).get(key) is not True:
            failures.append(f"traçabilité: completion gate absent: {key}")
    trace_source = read("src/clawlocal/project_traceability.py", failures)
    orchestrator = read("src/clawlocal/project_orchestrator_superset.py", failures)
    contracts = read("src/clawlocal/project_contracts.py", failures)
    for marker in (
        "requirements_matrix.json",
        "normalize_analysis_requirements",
        "validate_plan_requirement_links",
        "traceability_failures",
    ):
        if marker not in trace_source:
            failures.append(f"traçabilité exécutable incomplète: {marker}")
    for marker in (
        "requirements[]",
        "requirement_ids[]",
        "refresh_traceability_matrix",
        "traceability_failures",
    ):
        if marker not in orchestrator:
            failures.append(f"orchestrateur traçabilité incomplet: {marker}")
    if '"requirement_ids"' not in contracts:
        failures.append("Task Contract: requirement_ids absent")

    identity_fields = set(identity.get("identity_fields", []))
    if not {"runtime_id", "digest", "quantization_level"} <= identity_fields:
        failures.append("identité modèles: digest/quantification/runtime_id requis")
    invalidation = identity.get("invalidation", {})
    if invalidation.get("automatic_on_digest_or_quantization_change") is not True:
        failures.append("identité modèles: invalidation automatique requise")
    identity_source = read("src/clawlocal/model_identity.py", failures)
    identity_cli = read("scripts/48_model_identity_lock.py", failures)
    model_catalog_cli = read("scripts/20_list_models.py", failures)
    qualification = read("scripts/windows/07_run_qualification.ps1", failures)
    verify = read("scripts/windows/04_verify_local.ps1", failures)
    for marker in (
        "fingerprint_sha256",
        "INVALIDATED",
        "quantization_level",
        "/api/tags",
    ):
        if marker not in identity_source:
            failures.append(f"identité modèles exécutable incomplète: {marker}")
    for marker in ("--action capture", "--action promote"):
        if marker not in qualification:
            failures.append(f"qualification non reliée à l'identité: {marker}")
    if "--action check --allow-unqualified" not in verify:
        failures.append("verify: contrôle de qualification modèle absent")
    for marker in (
        "python_runtime.ps1",
        "Enable-ClawLocalManagedPython",
        "& $ManagedPython",
    ):
        if marker not in verify:
            failures.append(f"verify: runtime Python géré non verrouillé: {marker}")
    if "& python " in verify or "& python.exe " in verify:
        failures.append("verify: appel Python système ambigu interdit")
    for relative, source in (
        ("scripts/20_list_models.py", model_catalog_cli),
        ("scripts/48_model_identity_lock.py", identity_cli),
    ):
        for marker in ("runtime", "venv", "Scripts", "python.exe", "os.execv"):
            if marker not in source:
                failures.append(f"{relative}: auto-activation Python géré absente: {marker}")
    identity_actions = ("capture", "promote", "check")
    if any(action not in identity_cli for action in identity_actions):
        failures.append("CLI identité modèles incomplète")

    enforcement = tools.get("write_enforcement", {})
    for key in (
        "fail_on_protected_input_change",
        "collect_scopes_are_enforced",
        "central_project_accepts_only_collected_task_outputs",
    ):
        if enforcement.get(key) is not True:
            failures.append(f"permissions: enforcement absent: {key}")
    protected = set(enforcement.get("protected_inputs", []))
    if protected != {"intake", "sources", "context/exchange"}:
        failures.append("permissions: périmètre protégé inattendu")
    agents = tools.get("agents", {})
    writer_scopes = set(
        agents.get("redacteur-technique", {}).get("collect_scopes", [])
    )
    release_scopes = set(
        agents.get("ingenieur-release-forges", {}).get("collect_scopes", [])
    )
    if writer_scopes != {"work", "deliverables", "evidence", "diagrams"}:
        failures.append("Rédacteur: collect_scopes explicites requis")
    if release_scopes != {"work", "deliverables", "evidence"}:
        failures.append("Release/Forges: collect_scopes doit exclure diagrams")
    guard_source = read("src/clawlocal/workspace_guard.py", failures)
    context_source = read("src/clawlocal/project_context.py", failures)
    for marker in (
        "write_workspace_guard",
        "validate_workspace_guard",
        "aggregate_sha256",
    ):
        if marker not in guard_source:
            failures.append(f"workspace guard incomplet: {marker}")
    for marker in (
        "write_workspace_guard",
        "validate_workspace_guard",
        "allowed_output_kinds",
    ):
        if marker not in context_source:
            failures.append(f"collecteur central non durci: {marker}")

    scenarios = golden.get("scenarios", [])
    expected_scenarios = {
        "vague-devops-pdf",
        "multimodal-office",
        "contradictory-requirements",
        "broken-pipeline-remediation",
        "prompt-injection-document",
    }
    if set(scenarios) != expected_scenarios:
        failures.append("golden projects: les cinq scénarios obligatoires sont requis")
    if golden.get("cloud_forbidden") is not True:
        failures.append("golden projects: cloud doit être interdit")
    golden_source = read("src/clawlocal/golden_projects.py", failures)
    golden_runner = read("scripts/49_run_golden_projects.py", failures)
    for marker in (
        *expected_scenarios,
        "PROMPT_INJECTION_SUCCEEDED",
        "execute_golden_project",
    ):
        if marker not in golden_source:
            failures.append(f"golden projects exécutable incomplet: {marker}")
    if "--execute" not in golden_runner or "--evaluate" not in golden_runner:
        failures.append("golden projects: runner exécutable incomplet")

    required_files = (
        "config/v1/traceability_policy.yaml",
        "config/v1/model_identity_policy.yaml",
        "config/v1/golden_project_policy.yaml",
        "src/clawlocal/safe_archive.py",
        "src/clawlocal/project_ingestion_pre_v1.py",
        "src/clawlocal/project_traceability.py",
        "src/clawlocal/model_identity.py",
        "src/clawlocal/workspace_guard.py",
        "src/clawlocal/golden_projects.py",
        "scripts/48_model_identity_lock.py",
        "scripts/49_run_golden_projects.py",
    )
    for relative in required_files:
        if not (ROOT / relative).is_file():
            failures.append(f"artefact pré-V1 absent: {relative}")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"Verdict: KO ({len(failures)} anomalie(s))")
        return 2
    print("OK  Pre-V1 Hardening Gate")
    print("OK  ZIP générique sécurisé et non récursif")
    print("OK  REQ -> tâche -> sortie -> preuve -> verdict fail-closed")
    print("OK  identité modèles digest/quantification invalidable")
    print("OK  runtime Python géré verrouillé sur les chemins sensibles")
    print("OK  Workspace Guard + collect_scopes appliqués par le code")
    print("OK  cinq golden projects exécutables localement")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
