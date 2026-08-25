from __future__ import annotations

from dataclasses import dataclass

from clawlocal.config import load_contract


@dataclass(frozen=True)
class RouteDecision:
    agent: str
    route_kind: str
    model_alias: str
    reason: str


def select_route(
    agent: str,
    *,
    request_cloud: bool = False,
    cloud_enabled: bool = False,
    reason: str | None = None,
    specialist_available: bool = False,
) -> RouteDecision:
    routing = load_contract("model_routing.yaml")
    escalation = load_contract("escalation_policy.yaml")
    routes = routing["agents"]

    if agent not in routes:
        raise KeyError(f"Agent inconnu: {agent}")

    route = routes[agent]

    if not request_cloud:
        if specialist_available and route.get("local_specialist"):
            return RouteDecision(
                agent=agent,
                route_kind="local_specialist",
                model_alias=route["local_specialist"],
                reason="specialist_available",
            )
        return RouteDecision(
            agent=agent,
            route_kind="local_primary",
            model_alias=route["local_primary"],
            reason="local_first",
        )

    if not cloud_enabled:
        raise PermissionError("Escalade cloud demandée alors que le cloud est désactivé")
    if not reason:
        raise ValueError("Une raison explicite est obligatoire pour l'escalade cloud")

    triggers = escalation.get("triggers", {})
    if reason not in triggers:
        raise ValueError(f"Raison d'escalade inconnue: {reason}")

    trigger = triggers[reason]
    allowed_roles = set(trigger.get("allowed_roles", []))
    if allowed_roles and agent not in allowed_roles:
        raise PermissionError(f"Le rôle {agent} n'est pas autorisé pour le motif {reason}")

    return RouteDecision(
        agent=agent,
        route_kind="cloud_escalation",
        model_alias=route["cloud_escalation"],
        reason=reason,
    )
