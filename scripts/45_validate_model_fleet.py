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
    "sera-14b",
)

ACTIVE_TEXT_FILES = (
    "README.md",
    "STATUS.md",
    "docs/MODELES_LOCAUX.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/TELEMETRY.md",
    "config/openclaw.local.example.json5",
    "config/v1/model_catalog.yaml",
    "config/v1/model_routing.yaml",
    "config/v1/qualification_policy.yaml",
    "src/clawlocal/openclaw_config.py",
)


def load_yaml(name: str) -> dict[str, Any]:
    with (CONFIG / name).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return value


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
        failures.append("Auditeur: Qwen3.8 27B doit être l'alternative indépendante")
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

    decisions = {
        "chef-operations": "qwen-max",
        "expert-recherche": "qwen-max",
        "architecte-solutions": "gemma-deep",
        "ingenieur-devops": "devstral-devops",
        "ingenieur-securite": "qwen-max",
        "ingenieur-release-forges": "qwen-max",
        "redacteur-technique": "gemma-deep",
        "auditeur-qualite": "gemma-deep",
    }
    for agent, alias in decisions.items():
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

    openclaw_source = (ROOT / "src/clawlocal/openclaw_config.py").read_text(
        encoding="utf-8"
    )
    for marker in ('["qwen-max"]', '["gemma-deep"]'):
        if marker not in openclaw_source:
            failures.append(f"OpenClaw: modèle performance par défaut non câblé: {marker}")

    for relative in ACTIVE_TEXT_FILES:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"fichier actif attendu absent: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for runtime_id in FORBIDDEN_ACTIVE_RUNTIME_IDS:
            if runtime_id in text:
                failures.append(f"{relative}: ancien modèle local encore actif: {runtime_id}")

    for relative in ("README.md", "STATUS.md", "docs/MODELES_LOCAUX.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for runtime_id in EXPECTED_MODELS.values():
            if runtime_id not in text:
                failures.append(f"{relative}: modèle performance absent: {runtime_id}")

    if failures:
        print("Performance-only Model Fleet: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Performance-only Model Fleet: CONFORME")
    print("- Qwen 3.8 27B: orchestration/recherche/sécurité/release")
    print("- Gemma 4 26B: architecture/rédaction/audit")
    print("- Devstral Small 2 24B: DevOps/software engineering")
    print("- aucun Qwen 3.5 9B, Gemma 4 12B ou SERA 14B dans la flotte active")
    print("- les trois modèles sont obligatoires pour la qualification matérielle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
