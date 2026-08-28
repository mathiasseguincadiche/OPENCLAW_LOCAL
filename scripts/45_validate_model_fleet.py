from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from clawlocal.routing import select_route
from clawlocal.runtime import model_ref

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"

EXPECTED_MODELS = {
    "qwen-max": "qwen3.8:27b",
    "gemma-deep": "gemma4:26b",
    "devstral-devops": "devstral-small-2:24b",
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

FORBIDDEN_ACTIVE_RUNTIME_IDS = (
    "qwen3.5:9b",
    "gemma4:12b",
    "qwen3.5:27b",
    "sera-14b",
)

ACTIVE_MODEL_TEXT_FILES = (
    "README.md",
    "STATUS.md",
    "docs/ARCHITECTURE.md",
    "docs/BENCHMARK.md",
    "docs/MODELES_LOCAUX.md",
    "docs/OPENCLAW_INTEGRATION.md",
    "docs/OPERATIONS.md",
    "docs/QUALIFICATION.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/RUNTIME_BACKENDS.md",
    "docs/TROUBLESHOOTING.md",
    "config/openclaw.local.example.json5",
    "config/v1/model_catalog.yaml",
    "config/v1/model_routing.yaml",
    "config/v1/qualification_policy.yaml",
    "src/clawlocal/openclaw_config.py",
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
    "docs/QUALIFICATION.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/RUNTIME_BACKENDS.md",
    "docs/TROUBLESHOOTING.md",
)

FORBIDDEN_DOCUMENTATION_MARKERS = (
    "LOCAL_FAST",
    "-IncludeDeep",
    "-IncludeSpecialist",
    "-IncludeMax",
)


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


def main() -> int:
    failures: list[str] = []
    catalog = load_yaml("model_catalog.yaml")
    routing = load_yaml("model_routing.yaml")
    qualification = load_yaml("qualification_policy.yaml")
    models = catalog.get("models", {})
    agents = routing.get("agents", {})

    if set(models) != set(EXPECTED_MODELS):
        failures.append(
            "le catalogue local doit contenir exactement qwen-max, gemma-deep "
            "et devstral-devops"
        )

    policy = catalog.get("policy", {})
    if policy.get("performance_only") is not True:
        failures.append("model_catalog: performance_only doit être activé")
    if policy.get("local_model_count") != 3:
        failures.append("model_catalog: exactement trois modèles locaux supportés")
    if policy.get("no_hidden_small_model_fallback") is not True:
        failures.append("model_catalog: les petits fallbacks cachés doivent être interdits")

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

    allowed = set(EXPECTED_MODELS)
    for agent, expected in EXPECTED_PRIMARY.items():
        route = agents.get(agent, {})
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
    if auditor.get("independent_alternative") != "qwen-max":
        failures.append("Auditeur: Qwen 3.8 27B doit être l'alternative indépendante")
    if (
        auditor.get("independence_rule")
        != "reviewer_family_must_differ_from_producer_when_practical"
    ):
        failures.append("Auditeur: règle d'indépendance manquante")

    required = qualification.get("automated_gates", {}).get("required_models", [])
    if set(required) != allowed or len(required) != 3:
        failures.append("qualification: les trois modèles performance doivent être requis")
    fleet = qualification.get("supported_fleet", {})
    if set(fleet.get("exact_aliases", [])) != allowed:
        failures.append("qualification: supported_fleet doit contenir exactement trois alias")
    if fleet.get("all_models_required") is not True:
        failures.append("qualification: tous les modèles supportés doivent être requis")
    if fleet.get("allow_optional_local_models") is not False:
        failures.append("qualification: aucun quatrième modèle local optionnel n'est autorisé")
    if qualification.get("promotion", {}).get("automatic_promotion") is not False:
        failures.append("la qualification ne doit jamais auto-promouvoir un runtime/backend")

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

    openclaw_source = read_required("src/clawlocal/openclaw_config.py", failures)
    for marker in ('["qwen-max"]', '["gemma-deep"]'):
        if marker not in openclaw_source:
            failures.append(f"OpenClaw: modèle performance par défaut non câblé: {marker}")

    for relative in ACTIVE_MODEL_TEXT_FILES:
        text = read_required(relative, failures)
        for runtime_id in FORBIDDEN_ACTIVE_RUNTIME_IDS:
            if runtime_id in text:
                failures.append(f"{relative}: ancien modèle local encore actif: {runtime_id}")

    for relative in DOCUMENTATION_FILES:
        text = read_required(relative, failures)
        for marker in FORBIDDEN_DOCUMENTATION_MARKERS:
            if marker in text:
                failures.append(f"{relative}: marqueur documentaire legacy interdit: {marker}")

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

    qualification_runner = read_required(
        "scripts/windows/07_run_qualification.ps1", failures
    )
    for marker in ("IncludeDeep", "IncludeSpecialist", "IncludeMax"):
        if marker in qualification_runner:
            failures.append(f"runner qualification: switch legacy interdit: {marker}")

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

    if failures:
        print("Performance-only Model Fleet + Documentation: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Performance-only Model Fleet + Documentation: CONFORME")
    print("- Qwen 3.8 27B: orchestration/recherche/sécurité/release")
    print("- Gemma 4 26B: architecture/rédaction/audit")
    print("- Devstral Small 2 24B: DevOps/software engineering")
    print("- aucun runtime legacy dans les surfaces actives")
    print("- aucune commande de qualification legacy dans la documentation active")
    print("- OLLAMA_MODELS est câblé vers la racine gérée")
    print("- sauvegarde/restauration opérationnelles documentées")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
