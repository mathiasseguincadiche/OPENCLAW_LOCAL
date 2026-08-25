from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"


def load(name: str) -> dict:
    with (CONFIG / name).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return data


def main() -> int:
    failures: list[str] = []

    catalog = load("model_catalog.yaml")
    routing = load("model_routing.yaml")
    roles = load("role_matrix.yaml")
    escalation = load("escalation_policy.yaml")
    security = load("security.yaml")

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

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print(f"OK  rôles routés: {len(routed_agents)}")
    print(f"OK  modèles locaux déclarés: {len(model_ids)}")
    print(f"OK  routes cloud optionnelles: {len(cloud_ids)}")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
