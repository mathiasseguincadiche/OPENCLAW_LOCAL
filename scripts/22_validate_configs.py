from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: racine YAML invalide")
    return data


def main() -> int:
    failures: list[str] = []

    catalog = load(CONFIG / "model_catalog.yaml")
    routing = load(CONFIG / "model_routing.yaml")
    roles = load(CONFIG / "role_matrix.yaml")
    escalation = load(CONFIG / "escalation_policy.yaml")
    qualification = load(CONFIG / "qualification_policy.yaml")
    security = load(CONFIG / "security.yaml")
    suite_path = ROOT / "benchmarks" / "suites" / "devops_v1.yaml"
    suite = load(suite_path)

    model_ids = set(catalog.get("models", {}))
    cloud_ids = set(catalog.get("cloud_catalog", {}))
    role_ids = set(roles.get("roles", {}))
    routed_agents = set(routing.get("agents", {}))

    if role_ids != routed_agents:
        failures.append("les rôles et les agents routés ne correspondent pas exactement")

    if routing.get("cloud_enabled_by_default") is not False:
        failures.append("le cloud doit être désactivé par défaut")

    if escalation.get("default") != "deny":
        failures.append("la politique d'escalade doit être deny par défaut")

    if security.get("network", {}).get("local_model_loopback_only") is not True:
        failures.append("le provider local doit être loopback-only par défaut")

    for agent, route in routing.get("agents", {}).items():
        primary = route.get("local_primary")
        fallback = route.get("local_fallback")
        cloud = route.get("cloud_escalation")
        specialist = route.get("local_specialist")

        if primary not in model_ids:
            failures.append(f"{agent}: local_primary inconnu: {primary}")
        if fallback not in model_ids:
            failures.append(f"{agent}: local_fallback inconnu: {fallback}")
        if specialist is not None and specialist not in model_ids:
            failures.append(f"{agent}: local_specialist inconnu: {specialist}")
        if cloud not in cloud_ids:
            failures.append(f"{agent}: cloud_escalation inconnue: {cloud}")

    required_models = {
        key for key, value in catalog.get("models", {}).items() if value.get("required") is True
    }
    if not required_models:
        failures.append("aucun modèle local requis n'est déclaré")

    gate_models = set(qualification.get("automated_gates", {}).get("required_models", []))
    if gate_models != required_models:
        failures.append(
            "les modèles requis du catalogue et de la qualification doivent correspondre"
        )

    if qualification.get("promotion", {}).get("automatic_promotion") is not False:
        failures.append("la promotion automatique des modèles doit rester désactivée")

    if qualification.get("safety", {}).get("cloud_calls_allowed_during_qualification") is not False:
        failures.append("la qualification matérielle ne doit effectuer aucun appel cloud")

    contexts = qualification.get("required_contexts", [])
    if not contexts or any(int(context) <= 0 for context in contexts):
        failures.append("au moins un contexte de qualification positif est requis")

    if suite.get("id") != qualification.get("suite"):
        failures.append("la suite de benchmark ne correspond pas à qualification_policy.yaml")

    scenarios = suite.get("scenarios", [])
    if len(scenarios) < 8:
        failures.append("la suite de qualification doit contenir au moins huit scénarios")

    scenario_ids = [scenario.get("id") for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        failures.append("les identifiants de scénarios de benchmark doivent être uniques")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print(f"OK  rôles routés: {len(routed_agents)}")
    print(f"OK  modèles locaux déclarés: {len(model_ids)}")
    print(f"OK  routes cloud optionnelles: {len(cloud_ids)}")
    print(f"OK  scénarios qualification: {len(scenarios)}")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
