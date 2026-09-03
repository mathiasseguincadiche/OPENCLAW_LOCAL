from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from clawlocal.routing import select_route
from clawlocal.runtime import model_ref

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"

EXPECTED_MODELS = {
    "qwen-max": "qwen3.5:9b-q4_K_M",
    "gemma-deep": "gemma3:12b-it-q4_K_M",
    "devstral-devops": "qwen2.5-coder:14b-instruct-q4_K_M",
}
EXPECTED_CHALLENGERS = {
    "ministral-tool-calling": "ministral-3:14b-instruct-2512-q4_K_M",
}
EXPECTED_PRIMARY = {
    "chef-operations": "qwen-max",
    "expert-recherche": "qwen-max",
    "architecte-solutions": "gemma-deep",
    "ingenieur-devops": "devstral-devops",
    "ingenieur-securite": "qwen-max",
    "ingenieur-release-forges": "qwen-max",
    "redacteur-technique": "gemma-deep",
    "auditeur-qualite": "gemma-deep",
}

# Matching is deliberately case-insensitive so llama.cpp-normalized IDs such as
# :27B/:26B/:24B cannot bypass the retired-runtime gate.
FORBIDDEN_ACTIVE_RUNTIME_IDS = (
    "qwen3.8:27b",
    "gemma4:26b",
    "devstral-small-2:24b",
    "gemma4:12b",
    "qwen3.5:27b",
    "sera-14b",
)

ACTIVE_MODEL_TEXT_FILES = (
    "README.md",
    "STATUS.md",
    "docs/ARCHITECTURE.md",
    "docs/BENCHMARK.md",
    "docs/INSTALLATION_WINDOWS_11.md",
    "docs/MODELES_LOCAUX.md",
    "docs/OPENCLAW_INTEGRATION.md",
    "docs/OPERATIONS.md",
    "docs/PREMIERS_PAS_OPENCLAW_LOCAL.md",
    "docs/QUALIFICATION.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/RUNTIME_BACKENDS.md",
    "docs/TELEMETRY.md",
    "docs/TROUBLESHOOTING.md",
    "config/openclaw.local.example.json5",
    "config/v1/model_catalog.yaml",
    "config/v1/model_routing.yaml",
    "config/v1/qualification_policy.yaml",
    "config/v1/runtime_versions.json",
    "src/clawlocal/openclaw_config.py",
    "menu.ps1",
    "scripts/windows/04_verify_local.ps1",
    "scripts/windows/08_configure_openclaw.ps1",
    "scripts/windows/16_diagnose_intel_sycl_model.ps1",
    "scripts/windows/18_setup_intel_vulkan.ps1",
)

DOCUMENTATION_FILES = (
    "README.md",
    "STATUS.md",
    "docs/ARCHITECTURE.md",
    "docs/BENCHMARK.md",
    "docs/INSTALLATION_WINDOWS_11.md",
    "docs/MODELES_LOCAUX.md",
    "docs/OPENCLAW_INTEGRATION.md",
    "docs/OPERATIONS.md",
    "docs/PREMIERS_PAS_OPENCLAW_LOCAL.md",
    "docs/QUALIFICATION.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/RUNTIME_BACKENDS.md",
    "docs/TELEMETRY.md",
    "docs/TROUBLESHOOTING.md",
)
FORBIDDEN_DOCUMENTATION_COMMANDS = (
    "-IncludeDeep",
    "-IncludeSpecialist",
    "-IncludeMax",
)
ALLOWED_LOCAL_FAST_NEGATION = "aucun modèle LOCAL_FAST"


def load_yaml(name: str) -> dict[str, Any]:
    with (CONFIG / name).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return value


def read_required(path: str, failures: list[str]) -> str:
    target = ROOT / path
    if not target.is_file():
        failures.append(f"fichier actif attendu absent: {path}")
        return ""
    return target.read_text(encoding="utf-8")


def active_model_contract_files() -> tuple[str, ...]:
    files = list(ACTIVE_MODEL_TEXT_FILES)
    pester_root = ROOT / "tests" / "powershell"
    if pester_root.is_dir():
        files.extend(
            path.relative_to(ROOT).as_posix()
            for path in sorted(pester_root.glob("*.ps1"))
        )
    return tuple(files)


def validate_models(catalog: dict[str, Any], failures: list[str]) -> None:
    models = catalog.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODELS):
        failures.append(
            "le catalogue local routé doit contenir exactement qwen-max, "
            "gemma-deep et devstral-devops"
        )
        return

    policy = catalog.get("policy", {})
    if not isinstance(policy, dict):
        failures.append("model_catalog: policy invalide")
        return
    if policy.get("performance_only") is not True:
        failures.append("model_catalog: performance_only doit être activé")
    if policy.get("local_model_count") != 3:
        failures.append("model_catalog: exactement trois modèles locaux routés")
    if policy.get("no_hidden_small_model_fallback") is not True:
        failures.append("model_catalog: les petits fallbacks cachés doivent être interdits")
    if policy.get("target_hardware_profile") != "intel_arc_b580_12gb":
        failures.append("model_catalog: profil matériel B580 12GB requis")
    if policy.get("nominal_context_tokens") != 8192:
        failures.append("model_catalog: contexte nominal B580 doit rester à 8192")

    for alias, runtime_id in EXPECTED_MODELS.items():
        model = models.get(alias)
        if not isinstance(model, dict):
            failures.append(f"modèle performance absent: {alias}")
            continue
        if model.get("runtime_id") != runtime_id:
            failures.append(
                f"{alias}: runtime_id={model.get('runtime_id')} attendu={runtime_id}"
            )
        if model.get("provider") != "ollama":
            failures.append(f"{alias}: provider Ollama attendu")
        if model.get("required") is not True:
            failures.append(f"{alias}: doit être requis dans la flotte supportée")
        if model.get("routing_active") is not True:
            failures.append(f"{alias}: doit être routable")
        if model.get("quantization") != "Q4_K_M":
            failures.append(f"{alias}: quantification Q4_K_M requise pour la B580")
        if model.get("nominal_context_tokens") != 8192:
            failures.append(f"{alias}: contexte nominal 8192 attendu")
        if float(model.get("registry_size_gb", 99)) > 9.5:
            failures.append(f"{alias}: poids registre trop élevé pour la flotte B580")

    specialist = models.get("devstral-devops", {})
    if not isinstance(specialist, dict):
        return
    if specialist.get("family") != "qwen2-coder":
        failures.append("devstral-devops: runtime spécialiste doit être Qwen2.5 Coder")
    if specialist.get("compatibility_alias") is not True:
        failures.append("devstral-devops: alias de compatibilité doit être explicite")
    if specialist.get("input") != ["text"]:
        failures.append("devstral-devops: Qwen2.5 Coder doit rester text-only")
    if specialist.get("multimodal_handoff") != ["qwen-max", "gemma-deep"]:
        failures.append("devstral-devops: handoff multimodal Qwen/Gemma requis")


def validate_challenger(catalog: dict[str, Any], failures: list[str]) -> None:
    challengers = catalog.get("benchmark_challengers", {})
    if not isinstance(challengers, dict) or set(challengers) != set(
        EXPECTED_CHALLENGERS
    ):
        failures.append(
            "model_catalog: Ministral doit être l'unique challenger de benchmark déclaré"
        )
        return
    challenger = challengers.get("ministral-tool-calling")
    if not isinstance(challenger, dict):
        failures.append("model_catalog: challenger Ministral invalide")
        return
    expected_runtime = EXPECTED_CHALLENGERS["ministral-tool-calling"]
    if challenger.get("runtime_id") != expected_runtime:
        failures.append("Ministral challenger: runtime Q4_K_M exact attendu")
    if challenger.get("provider") != "ollama":
        failures.append("Ministral challenger: provider Ollama attendu")
    if challenger.get("quantization") != "Q4_K_M":
        failures.append("Ministral challenger: Q4_K_M requis")
    if challenger.get("registry_size_gb") != 9.1:
        failures.append("Ministral challenger: poids registre 9.1 Go attendu")
    if challenger.get("nominal_context_tokens") != 8192:
        failures.append("Ministral challenger: contexte de comparaison 8192 attendu")
    if challenger.get("required_for_selection") is not True:
        failures.append("Ministral challenger: comparaison obligatoire avant sélection")
    if challenger.get("routing_active") is not False:
        failures.append("Ministral challenger: doit rester hors routage nominal")
    if challenger.get("incumbent_alias") != "gemma-deep":
        failures.append("Ministral challenger: doit challenger gemma-deep")
    if challenger.get("automatic_promotion") is not False:
        failures.append("Ministral challenger: promotion automatique interdite")
    scope = challenger.get("challenge_scope", [])
    if not isinstance(scope, list) or not {
        "native_tool_calling",
        "tool_feedback_repair",
    }.issubset(set(scope)):
        failures.append("Ministral challenger: tool-calling et réparation obligatoires")


def validate_routing(routing: dict[str, Any], failures: list[str]) -> None:
    agents = routing.get("agents", {})
    if not isinstance(agents, dict):
        failures.append("model_routing: agents invalide")
        return
    allowed = set(EXPECTED_MODELS)
    for agent, expected in EXPECTED_PRIMARY.items():
        route = agents.get(agent, {})
        if not isinstance(route, dict):
            failures.append(f"{agent}: route absente")
            continue
        if route.get("local_primary") != expected:
            failures.append(f"{agent}: local_primary doit être {expected}")
        for field in (
            "local_primary",
            "local_fallback",
            "local_specialist",
            "local_deep",
            "local_max",
            "independent_alternative",
        ):
            alias = route.get(field)
            if alias is not None and alias not in allowed:
                failures.append(f"{agent}: {field} référence un modèle non supporté: {alias}")

    auditor = agents.get("auditeur-qualite", {})
    if isinstance(auditor, dict):
        if auditor.get("independent_alternative") != "qwen-max":
            failures.append("Auditeur: Qwen 3.5 9B doit être l'alternative indépendante")
        if (
            auditor.get("independence_rule")
            != "reviewer_family_must_differ_from_producer_when_practical"
        ):
            failures.append("Auditeur: règle d'indépendance manquante")


def validate_qualification(
    qualification: dict[str, Any], failures: list[str]
) -> None:
    allowed = set(EXPECTED_MODELS)
    automated = qualification.get("automated_gates", {})
    if not isinstance(automated, dict):
        failures.append("qualification: automated_gates invalide")
        return
    required = automated.get("required_models", [])
    if set(required) != allowed or len(required) != 3:
        failures.append("qualification: les trois modèles routés doivent être requis")

    fleet = qualification.get("supported_fleet", {})
    if not isinstance(fleet, dict):
        failures.append("qualification: supported_fleet invalide")
    else:
        if set(fleet.get("exact_aliases", [])) != allowed:
            failures.append("qualification: supported_fleet doit contenir trois alias")
        if fleet.get("all_models_required") is not True:
            failures.append("qualification: tous les modèles routés doivent être requis")
        if fleet.get("allow_optional_local_models") is not False:
            failures.append("qualification: aucun quatrième modèle routé optionnel")
        if fleet.get("benchmark_challengers_count_as_routed_models") is not False:
            failures.append("qualification: challenger ne doit pas compter comme modèle routé")

    promotion = qualification.get("promotion", {})
    if not isinstance(promotion, dict) or promotion.get("automatic_promotion") is not False:
        failures.append("qualification: aucune auto-promotion du runtime/backend")

    challenge = qualification.get("model_selection_challenger", {})
    if not isinstance(challenge, dict):
        failures.append("qualification: gate challenger absent")
        return
    expected_runtime = EXPECTED_CHALLENGERS["ministral-tool-calling"]
    expected = {
        "required_before_manual_model_selection": True,
        "incumbent_alias": "gemma-deep",
        "challenger_alias": "ministral-tool-calling",
        "challenger_runtime_id": expected_runtime,
        "context_tokens": 8192,
        "repetitions": 3,
        "protocol": "native_tool_calling_v1",
        "automatic_promotion": False,
        "human_decision_required": True,
        "evidence_required": True,
    }
    for key, value in expected.items():
        if challenge.get(key) != value:
            failures.append(f"qualification challenger: {key}={value!r} requis")
    capabilities = challenge.get("required_capabilities", [])
    if set(capabilities) != {"native_tool_calling", "tool_feedback_repair"}:
        failures.append("qualification challenger: capacités tool-calling incomplètes")


def validate_runtime_routes(failures: list[str]) -> None:
    for agent, alias in EXPECTED_PRIMARY.items():
        decision = select_route(agent, qualified_models=set())
        if decision.model_alias != alias:
            failures.append(f"{agent}: route nominale {alias} attendue")

    independent = select_route(
        "auditeur-qualite",
        producer_model_alias="gemma-deep",
        qualified_models=set(),
    )
    if independent.model_alias != "qwen-max" or independent.route_kind != "local_independent":
        failures.append("Auditeur: production Gemma doit être revue par la famille Qwen")

    for alias, runtime_id in EXPECTED_MODELS.items():
        if model_ref(alias) != f"ollama/{runtime_id}":
            failures.append(f"{alias}: résolution runtime incohérente")


def validate_active_surfaces(failures: list[str]) -> None:
    openclaw_source = read_required("src/clawlocal/openclaw_config.py", failures)
    for marker in ('["qwen-max"]', '["gemma-deep"]'):
        if marker not in openclaw_source:
            failures.append(f"OpenClaw: modèle performance non câblé: {marker}")
    if 'model.get("nominal_context_tokens", 8192)' not in openclaw_source:
        failures.append("OpenClaw: contexte nominal par modèle non câblé")

    for relative in active_model_contract_files():
        text = read_required(relative, failures)
        folded = text.casefold()
        for runtime_id in FORBIDDEN_ACTIVE_RUNTIME_IDS:
            if runtime_id.casefold() in folded:
                failures.append(f"{relative}: ancien modèle local encore actif: {runtime_id}")

    for relative in DOCUMENTATION_FILES:
        text = read_required(relative, failures)
        for marker in FORBIDDEN_DOCUMENTATION_COMMANDS:
            if marker in text:
                failures.append(f"{relative}: commande documentaire legacy: {marker}")
        local_fast_count = text.count("LOCAL_FAST")
        allowed_negations = text.count(ALLOWED_LOCAL_FAST_NEGATION)
        if local_fast_count != allowed_negations:
            failures.append(f"{relative}: taxonomie LOCAL_FAST legacy encore active")

    for relative in (
        "README.md",
        "STATUS.md",
        "docs/ARCHITECTURE.md",
        "docs/MODELES_LOCAUX.md",
        "docs/QUALIFICATION.md",
    ):
        text = read_required(relative, failures)
        for runtime_id in EXPECTED_MODELS.values():
            if runtime_id not in text:
                failures.append(f"{relative}: modèle performance absent: {runtime_id}")


def validate_operator_contracts(failures: list[str]) -> None:
    qualification_runner = read_required(
        "scripts/windows/07_run_qualification.ps1", failures
    )
    for marker in ("IncludeDeep", "IncludeSpecialist", "IncludeMax"):
        if marker in qualification_runner:
            failures.append(f"runner qualification: switch legacy interdit: {marker}")

    challenger_runner = read_required(
        "scripts/52_compare_tool_calling_models.py", failures
    )
    challenger_windows = read_required(
        "scripts/windows/23_compare_model_challenger.ps1", failures
    )
    for marker in (
        "native_tool_calling_v1",
        "PROMOTION_ALLOWED=false",
        "MANUAL_DECISION_REQUIRED=true",
    ):
        if marker not in challenger_runner:
            failures.append(f"runner challenger: marqueur obligatoire absent: {marker}")
    if "Enable-ClawLocalManagedPython" not in challenger_windows:
        failures.append("runner challenger Windows: Python géré obligatoire")
    if "ministral-3:14b-instruct-2512-q4_K_M" not in challenger_windows:
        failures.append("runner challenger Windows: runtime Ministral exact absent")

    configure_local = read_required("scripts/windows/02_configure_local.ps1", failures)
    pull_models = read_required("scripts/windows/03_pull_models.ps1", failures)
    install_doc = read_required("docs/INSTALLATION_WINDOWS_11.md", failures)
    for relative, text in (
        ("scripts/windows/02_configure_local.ps1", configure_local),
        ("scripts/windows/03_pull_models.ps1", pull_models),
        ("docs/INSTALLATION_WINDOWS_11.md", install_doc),
    ):
        if "OLLAMA_MODELS" not in text:
            failures.append(f"{relative}: OLLAMA_MODELS doit être documenté/câblé")
        if "models\\ollama" not in text:
            failures.append(f"{relative}: racine models\\ollama attendue")

    operations = read_required("docs/OPERATIONS.md", failures)
    for marker in ("projects", "state", "proofs", "Restauration"):
        if marker not in operations:
            failures.append(f"docs/OPERATIONS.md: sauvegarde/restauration incomplète: {marker}")


def main() -> int:
    failures: list[str] = []
    catalog = load_yaml("model_catalog.yaml")
    routing = load_yaml("model_routing.yaml")
    qualification = load_yaml("qualification_policy.yaml")

    validate_models(catalog, failures)
    validate_challenger(catalog, failures)
    validate_routing(routing, failures)
    validate_qualification(qualification, failures)
    validate_runtime_routes(failures)
    validate_active_surfaces(failures)
    validate_operator_contracts(failures)

    if failures:
        print("B580-sized Model Fleet + Challenger: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("B580-sized Model Fleet + Challenger: CONFORME")
    print("- Qwen 3.5 9B Q4_K_M: orchestration/recherche/sécurité/release")
    print("- Gemma 3 12B Q4_K_M: architecture/rédaction/audit/multimodal")
    print("- Qwen 2.5 Coder 14B Q4_K_M: DevOps/software engineering")
    print("- exactement trois modèles restent routés et requis")
    print("- Ministral 3 14B Q4_K_M est challenger obligatoire de Gemma")
    print("- comparaison native tool-calling + réparation, 3 répétitions à 8K")
    print("- challenger hors routage; promotion automatique interdite")
    print("- aucun runtime legacy dans les surfaces actives ou tests Pester")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
