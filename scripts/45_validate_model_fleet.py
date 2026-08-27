from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from clawlocal.routing import select_route
from clawlocal.runtime import model_ref

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"

EXPECTED_RUNTIME_IDS = {
    "qwen-general": "qwen3.5:9b",
    "gemma-review": "gemma4:12b",
    "gemma-deep": "gemma4:26b",
    "devstral-devops": "devstral-small-2:24b",
    "qwen-max": "qwen3.8:27b",
}

EXPECTED_DEFAULT_TIERS = {
    "chef-operations": "max",
    "expert-recherche": "max",
    "architecte-solutions": "deep",
    "ingenieur-devops": "specialist",
    "ingenieur-securite": "max",
    "ingenieur-release-forges": "primary",
    "redacteur-technique": "deep",
    "auditeur-qualite": "deep",
}

EXPECTED_QUALIFICATION_CLASSES = {
    "devstral-devops": "local_specialist",
    "gemma-deep": "local_deep",
    "qwen-max": "local_max",
}


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

    for alias, runtime_id in EXPECTED_RUNTIME_IDS.items():
        model = models.get(alias)
        if not isinstance(model, dict):
            failures.append(f"modèle requis par la flotte absent: {alias}")
            continue
        if model.get("runtime_id") != runtime_id:
            failures.append(
                f"{alias}: runtime_id={model.get('runtime_id')} attendu={runtime_id}"
            )
        if model.get("provider") != "ollama":
            failures.append(f"{alias}: provider Ollama attendu")

    for alias in ("qwen-general", "gemma-review"):
        if models.get(alias, {}).get("required") is not True:
            failures.append(f"{alias}: le modèle fast doit rester requis")

    for alias, expected_class in EXPECTED_QUALIFICATION_CLASSES.items():
        model = models.get(alias, {})
        if model.get("required") is not False:
            failures.append(f"{alias}: doit rester optionnel avant qualification B580")
        if model.get("status") != "optional_candidate":
            failures.append(f"{alias}: status optional_candidate attendu")
        if model.get("activation") != "benchmark_required":
            failures.append(f"{alias}: activation benchmark_required obligatoire")
        if model.get("class") != expected_class:
            failures.append(f"{alias}: classe {expected_class} attendue")

    sera = models.get("sera-devops", {})
    if sera.get("routing_active") is not False:
        failures.append("SERA doit rester hors routage actif tant que son backend n'est pas qualifié")

    if routing.get("routing_order") != [
        "local_primary",
        "local_specialist",
        "local_deep",
        "local_max",
        "cloud_escalation",
    ]:
        failures.append("ordre de routage local-first inattendu")

    for agent, tier in EXPECTED_DEFAULT_TIERS.items():
        route = agents.get(agent, {})
        if route.get("default_preferred_tier") != tier:
            failures.append(f"{agent}: default_preferred_tier={tier} attendu")

    if agents.get("ingenieur-devops", {}).get("local_specialist") != "devstral-devops":
        failures.append("DevOps doit utiliser Devstral Small 2 comme spécialiste qualifiable")
    if agents.get("architecte-solutions", {}).get("local_deep") != "gemma-deep":
        failures.append("Architecte doit utiliser Gemma 4 26B comme deep qualifiable")
    if agents.get("redacteur-technique", {}).get("local_deep") != "gemma-deep":
        failures.append("Rédacteur doit utiliser Gemma 4 26B comme deep qualifiable")

    auditor = agents.get("auditeur-qualite", {})
    if auditor.get("local_primary") != "gemma-review":
        failures.append("Auditeur: Gemma 4 12B doit être le primaire indépendant")
    if auditor.get("independent_alternative") != "qwen-max":
        failures.append("Auditeur: Qwen3.8 27B doit être l'alternative indépendante max")
    if auditor.get("independence_rule") != "reviewer_family_must_differ_from_producer_when_practical":
        failures.append("Auditeur: règle d'indépendance manquante")

    specialists = qualification.get("specialists", {})
    for alias in EXPECTED_QUALIFICATION_CLASSES:
        entry = specialists.get(alias, {})
        if entry.get("evaluate_after_required_models") is not True:
            failures.append(f"{alias}: qualification optionnelle active attendue")
        if entry.get("promotion_requires_separate_review") is not True:
            failures.append(f"{alias}: promotion séparée obligatoire")
    if specialists.get("sera-devops", {}).get("routing_active") is not False:
        failures.append("qualification SERA: routage doit rester inactif")
    promotion = qualification.get("promotion", {})
    if promotion.get("automatic_promotion") is not False:
        failures.append("la qualification ne doit jamais auto-promouvoir un modèle")
    if promotion.get("runtime_activation_env") != "OPENCLAW_LOCAL_QUALIFIED_MODELS":
        failures.append("variable runtime de qualification incohérente")

    fast = select_route("chef-operations", qualified_models=set())
    if fast.model_alias != "qwen-general" or fast.route_kind != "local_primary":
        failures.append("un candidat non qualifié ne doit jamais remplacer le fast requis")

    maximum = select_route("chef-operations", qualified_models={"qwen-max"})
    if maximum.model_alias != "qwen-max" or maximum.route_kind != "local_max":
        failures.append("Qwen3.8 qualifié doit devenir la route max du Chef")

    devops = select_route("ingenieur-devops", qualified_models={"devstral-devops"})
    if devops.model_alias != "devstral-devops" or devops.route_kind != "local_specialist":
        failures.append("Devstral qualifié doit devenir le spécialiste DevOps")

    architect = select_route("architecte-solutions", qualified_models={"gemma-deep"})
    if architect.model_alias != "gemma-deep" or architect.route_kind != "local_deep":
        failures.append("Gemma 4 26B qualifié doit devenir le deep Architecte")

    independent = select_route(
        "auditeur-qualite",
        producer_model_alias="gemma-review",
        qualified_models=set(),
    )
    if independent.model_alias != "qwen-general" or independent.route_kind != "local_independent":
        failures.append("l'Auditeur doit changer de famille face à un producteur Gemma")

    for alias, runtime_id in EXPECTED_RUNTIME_IDS.items():
        expected = f"ollama/{runtime_id}"
        if model_ref(alias) != expected:
            failures.append(f"{alias}: résolution runtime incohérente")

    runtime_source = (ROOT / "src" / "clawlocal" / "runtime.py").read_text(encoding="utf-8")
    qualification_source = (ROOT / "src" / "clawlocal" / "qualification.py").read_text(encoding="utf-8")
    benchmark_source = (ROOT / "scripts" / "benchmark_local.py").read_text(encoding="utf-8")
    if "OPENCLAW_LOCAL_QUALIFIED_MODELS" not in runtime_source:
        failures.append("promotion locale: registre runtime des modèles qualifiés absent")
    if "optional_candidates" not in qualification_source:
        failures.append("qualification: verdict indépendant des candidats optionnels absent")
    for flag in ("--include-specialist", "--include-deep", "--include-max"):
        if flag not in benchmark_source:
            failures.append(f"benchmark: option absente: {flag}")

    if failures:
        print("Model Fleet August 2026: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Model Fleet August 2026: CONFORME")
    print("- fast: Qwen3.5 9B + Gemma 4 12B")
    print("- specialist: Devstral Small 2 24B (après qualification)")
    print("- deep: Gemma 4 26B A4B (après qualification)")
    print("- max: Qwen3.8 27B (après qualification)")
    print("- reviewer independence: Gemma/Qwen family separation")
    print("- optional candidates: benchmarkés et scorés séparément")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
