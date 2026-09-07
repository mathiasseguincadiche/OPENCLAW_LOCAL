from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"
SUPPORTED_CHECKS = {
    "nonempty",
    "contains_all",
    "contains_any",
    "not_contains_any",
    "json_keys",
    "yaml_keys",
}
EXPECTED_PROJECT_STATES = [
    "INTAKE_READY",
    "ANALYZED",
    "CLARIFICATION_REQUIRED",
    "PLANNED",
    "ASSIGNED",
    "IN_PROGRESS",
    "VALIDATING",
    "REVIEW",
    "PACKAGING",
    "COMPLETE",
]


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: racine YAML invalide")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: racine JSON invalide")
    return data


def validate_platform_versions(
    contracts: dict[str, dict[str, Any]],
    repository_version: str,
    failures: list[str],
) -> None:
    for name, contract in contracts.items():
        value = contract.get("platform_version")
        if value is not None and str(value) != repository_version:
            failures.append(
                f"{name}: platform_version={value} != VERSION={repository_version}"
            )


def validate_orchestrator(
    orchestration: dict[str, Any],
    project: dict[str, Any],
    role_ids: set[str],
    failures: list[str],
) -> None:
    states = orchestration.get("status_flow", [])
    if states != EXPECTED_PROJECT_STATES:
        failures.append("orchestration_policy.yaml: status_flow inattendu")
    if project.get("status_flow") != states:
        failures.append("project_policy.yaml et orchestration_policy.yaml divergent")

    engine = orchestration.get("engine", {})
    if engine.get("fail_closed") is not True:
        failures.append("Project Orchestrator doit rester fail-closed")
    if engine.get("automatic_cloud_escalation") is not False:
        failures.append("Project Orchestrator ne doit jamais auto-escalader vers le cloud")
    if engine.get("source_repository_is_ground_truth") is not True:
        failures.append("Project Orchestrator doit conserver le dépôt source comme vérité")
    if engine.get("final_human_approval_required") is not True:
        failures.append("Project Orchestrator doit exiger l'approbation humaine finale")

    transitions = orchestration.get("transitions", {})
    if set(transitions) != set(states):
        failures.append("orchestration_policy.yaml: transitions incomplètes")
    for source, targets in transitions.items():
        if not isinstance(targets, list):
            failures.append(f"orchestration: transitions {source} doit être une liste")
            continue
        for target in targets:
            if target not in states:
                failures.append(f"orchestration: transition vers état inconnu: {target}")
    if transitions.get("COMPLETE") != []:
        failures.append("COMPLETE doit être un état terminal")

    phases = orchestration.get("phases", {})
    allowed_phase_owners = role_ids | {"human", "assigned_agent"}
    for phase_id, phase in phases.items():
        owner = str(phase.get("owner", ""))
        if owner not in allowed_phase_owners:
            failures.append(f"orchestration phase {phase_id}: owner inconnu: {owner}")
        reviewers = phase.get("reviewers", [])
        if not isinstance(reviewers, list) or not set(reviewers) <= role_ids:
            failures.append(f"orchestration phase {phase_id}: reviewers invalides")

    execution = orchestration.get("execution", {})
    if execution.get("local_first") is not True:
        failures.append("Project Orchestrator doit rester local-first")
    if int(execution.get("max_parallel_tasks", 0)) != 1:
        failures.append("V0.2: exécution projet doit rester séquentielle par défaut")
    if int(execution.get("max_task_attempts", 0)) < 1:
        failures.append("Project Orchestrator exige au moins une tentative par tâche")
    if execution.get("collect_task_outputs") is not True:
        failures.append("Project Orchestrator doit collecter les sorties de tâches")
    if execution.get("task_output_namespaced_by_task") is not True:
        failures.append("sorties de tâches doivent être namespacées")


def validate_local_only_models(
    catalog: dict[str, Any],
    routing: dict[str, Any],
    qualification: dict[str, Any],
    failures: list[str],
) -> None:
    policy = catalog.get("policy", {})
    if policy.get("local_first") is not True or policy.get("local_only") is not True:
        failures.append("Architecture V2: model_catalog doit être local-first/local-only")
    if policy.get("cloud_models_supported") is not False:
        failures.append("Architecture V2: cloud_models_supported doit être false")
    if catalog.get("cloud_catalog"):
        failures.append("Architecture V2: aucun cloud_catalog n'est autorisé")

    model_ids = set(catalog.get("models", {}))
    if model_ids != {"qwen-max", "gemma-deep", "devstral-devops"}:
        failures.append("Architecture V2: exactement trois alias locaux sont supportés")
    runtime_ids: list[str] = []
    for alias, model in catalog.get("models", {}).items():
        runtime_id = str(model.get("runtime_id", ""))
        if not runtime_id:
            failures.append(f"{alias}: runtime_id absent")
        runtime_ids.append(runtime_id)
        if model.get("provider") != "ollama":
            failures.append(f"{alias}: provider Ollama local attendu")
        if model.get("quantization") != "Q4_K_M":
            failures.append(f"{alias}: Q4_K_M requis")
    if len(runtime_ids) != len(set(runtime_ids)):
        failures.append("les runtime_id locaux doivent être uniques")

    if routing.get("local_only") is not True:
        failures.append("Architecture V2: model_routing local_only=true requis")
    if "cloud_enabled_by_default" in routing:
        failures.append("Architecture V2: cloud_enabled_by_default doit être supprimé")
    if "cloud_escalation" in routing.get("routing_order", []):
        failures.append("Architecture V2: cloud_escalation interdite dans routing_order")
    for agent, route in routing.get("agents", {}).items():
        if "cloud_escalation" in route:
            failures.append(f"{agent}: route de modèle cloud interdite")
        for field in (
            "local_primary",
            "local_fallback",
            "local_specialist",
            "local_deep",
            "local_max",
            "independent_alternative",
        ):
            alias = route.get(field)
            if alias is not None and alias not in model_ids:
                failures.append(f"{agent}: {field} inconnu: {alias}")

    required_models = {
        key
        for key, value in catalog.get("models", {}).items()
        if value.get("required") is True
    }
    gate_models = set(
        qualification.get("automated_gates", {}).get("required_models", [])
    )
    if gate_models != required_models or len(required_models) != 3:
        failures.append("qualification: les trois modèles locaux requis doivent correspondre")
    safety = qualification.get("safety", {})
    if safety.get("cloud_calls_allowed_during_qualification") is not False:
        failures.append("qualification: aucun appel LLM cloud")
    if safety.get("cloud_models_supported") is not False or safety.get("local_only") is not True:
        failures.append("qualification: contrat local-only V2 requis")


def main() -> int:
    failures: list[str] = []
    repository_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    catalog = load(CONFIG / "model_catalog.yaml")
    routing = load(CONFIG / "model_routing.yaml")
    roles = load(CONFIG / "role_matrix.yaml")
    qualification = load(CONFIG / "qualification_policy.yaml")
    security = load(CONFIG / "security.yaml")
    tools = load(CONFIG / "tool_policy.yaml")
    platform = load(CONFIG / "platform.yaml")
    project = load(CONFIG / "project_policy.yaml")
    orchestration = load(CONFIG / "orchestration_policy.yaml")
    web = load(CONFIG / "web_policy.yaml")
    backends = load(CONFIG / "runtime_backends.yaml")
    diagrams = load(CONFIG / "diagram_policy.yaml")
    runtime = load_json(CONFIG / "runtime_versions.json")

    contracts = {
        "model_catalog.yaml": catalog,
        "model_routing.yaml": routing,
        "role_matrix.yaml": roles,
        "qualification_policy.yaml": qualification,
        "security.yaml": security,
        "tool_policy.yaml": tools,
        "platform.yaml": platform,
        "project_policy.yaml": project,
        "orchestration_policy.yaml": orchestration,
        "web_policy.yaml": web,
        "runtime_backends.yaml": backends,
        "diagram_policy.yaml": diagrams,
    }
    validate_platform_versions(contracts, repository_version, failures)
    if str(runtime.get("platform_version")) != repository_version:
        failures.append("runtime_versions.json: platform_version incohérente")

    role_ids = set(roles.get("roles", {}))
    routed_agents = set(routing.get("agents", {}))
    tool_agents = set(tools.get("agents", {}))
    if role_ids != routed_agents:
        failures.append("les rôles et agents routés doivent correspondre exactement")
    if role_ids != tool_agents:
        failures.append("la politique d'outils doit couvrir exactement les huit rôles")

    validate_local_only_models(catalog, routing, qualification, failures)

    if security.get("network", {}).get("local_model_loopback_only") is not True:
        failures.append("le provider local doit être loopback-only par défaut")

    suite_id = str(qualification.get("suite", "")).strip()
    suite_path = ROOT / "benchmarks" / "suites" / f"{suite_id.replace('-', '_')}.yaml"
    if not suite_id or not suite_path.is_file():
        failures.append(f"suite de qualification introuvable: {suite_id or '<vide>'}")
        suite: dict[str, Any] = {}
    else:
        suite = load(suite_path)
    scenarios = suite.get("scenarios", []) if suite else []
    if len(scenarios) < 10:
        failures.append("devops-v2 doit contenir au moins dix scénarios")
    scenario_ids = [scenario.get("id") for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        failures.append("les identifiants de scénarios doivent être uniques")
    for scenario in scenarios:
        for check in scenario.get("checks", []):
            if check.get("type") not in SUPPORTED_CHECKS:
                failures.append(
                    f"{scenario.get('id')}: check non supporté: {check.get('type')}"
                )

    defaults = tools.get("security_defaults", {})
    if defaults.get("fs_workspace_only") is not True:
        failures.append("tools.fs.workspaceOnly doit rester activé")
    if defaults.get("exec_mode") != "ask":
        failures.append("le mode exec global doit rester ask")
    if defaults.get("elevated_enabled") is not False:
        failures.append("le mode elevated doit rester désactivé")

    review_roles = {
        "chef-operations",
        "expert-recherche",
        "architecte-solutions",
        "auditeur-qualite",
    }
    required_denies = {"write", "edit", "apply_patch", "exec", "process"}
    for agent in review_roles:
        denied = set(tools.get("agents", {}).get(agent, {}).get("deny", []))
        if not required_denies <= denied:
            failures.append(f"{agent}: posture de revue insuffisamment restrictive")

    project_rules = project.get("rules", {})
    if project_rules.get("overwrite_existing_project") is not False:
        failures.append("Project Intake ne doit pas écraser un projet existant")
    if project_rules.get("source_repository_is_ground_truth") is not True:
        failures.append("le dépôt source doit rester la vérité du projet")
    if project_rules.get("rag_does_not_replace_file_reading") is not True:
        failures.append("le RAG ne doit pas remplacer la lecture des fichiers réels")
    if project_rules.get("state_changes_require_evidence") is not True:
        failures.append("les changements d'état projet doivent exiger des preuves")
    if project_rules.get("final_completion_requires_human_approval") is not True:
        failures.append("COMPLETE doit exiger une validation humaine")

    validate_orchestrator(orchestration, project, role_ids, failures)

    if web.get("local_first") is not True:
        failures.append("la recherche Web doit rester local-first")
    web_nominal = web.get("nominal_path", {})
    if web_nominal.get("reasoning") != "local_model":
        failures.append("le raisonnement après recherche Web doit rester local")
    if web_nominal.get("web_search_enabled") is not True:
        failures.append("web_search doit être activé dans le parcours nominal")
    if web_nominal.get("web_fetch_enabled") is not True:
        failures.append("web_fetch doit être activé dans le parcours nominal")

    backend_catalog = backends.get("backends", {})
    nominal_backend = platform.get("local_provider", {}).get("nominal_id")
    if nominal_backend not in backend_catalog:
        failures.append("platform.yaml: backend nominal absent")
    for backend_id, backend in backend_catalog.items():
        if backend.get("windows_native") is not True:
            failures.append(f"{backend_id}: backend non Windows natif")
        endpoint = str(backend.get("endpoint", ""))
        if endpoint and "127.0.0.1" not in endpoint and "localhost" not in endpoint:
            failures.append(f"{backend_id}: endpoint non loopback: {endpoint}")

    diagram_policy = diagrams.get("policy", {})
    if diagram_policy.get("diagram_as_code_first") is not True:
        failures.append("les schémas doivent rester diagram-as-code")
    if diagram_policy.get("renderer_must_be_local") is not True:
        failures.append("les renderers de diagrammes doivent rester locaux")

    if runtime.get("schema_version") != "1.0.0":
        failures.append("runtime_versions.json doit utiliser schema_version 1.0.0")
    python_supported = set(runtime.get("python", {}).get("supported", []))
    if not {"3.12", "3.13"} <= python_supported:
        failures.append("Python 3.12 et 3.13 doivent être supportés")
    if runtime.get("qualification", {}).get("real_run_required") is not True:
        failures.append("le runtime doit exiger une qualification matérielle réelle")
    if runtime.get("qualification", {}).get("promotion_from_ci_forbidden") is not True:
        failures.append("la promotion depuis la CI doit rester interdite")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print(f"OK  version plateforme: {repository_version}")
    print(f"OK  rôles routés/outillés: {len(routed_agents)}")
    print("OK  Architecture V2: exactement trois modèles locaux, aucun modèle cloud")
    print(f"OK  scénarios qualification: {len(scenarios)} ({suite_id})")
    print(f"OK  backends locaux déclarés: {len(backend_catalog)}")
    print(f"OK  Project Orchestrator: {len(EXPECTED_PROJECT_STATES)} états fail-closed")
    print("OK  Project Intake / Web local-first / diagrammes locaux")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
