from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clawlocal.config import load_contract


@dataclass(frozen=True)
class RouteDecision:
    agent: str
    route_kind: str
    model_alias: str
    reason: str


def _enforce_trigger_conditions(
    trigger: dict[str, Any],
    *,
    local_web_attempted: bool,
    source_conflict_observed: bool,
    failure_evidence: bool,
    local_attempts: int,
    human_approved: bool,
) -> None:
    precondition = trigger.get("precondition")
    if precondition == "local_web_attempted" and not local_web_attempted:
        raise PermissionError("escalade refusée: tentative Web locale requise")
    if precondition == "local_web_sources_conflict" and not source_conflict_observed:
        raise PermissionError("escalade refusée: conflit de sources Web non démontré")
    if trigger.get("require_failure_evidence") is True and not failure_evidence:
        raise PermissionError("escalade refusée: preuve d'échec local requise")

    max_local_attempts = trigger.get("max_local_attempts")
    if max_local_attempts is not None and local_attempts < int(max_local_attempts):
        raise PermissionError(
            "escalade refusée: "
            f"{local_attempts} tentative(s) locale(s), "
            f"{int(max_local_attempts)} requise(s)"
        )
    if trigger.get("require_human_approval") is True and not human_approved:
        raise PermissionError("escalade refusée: approbation humaine requise")


def select_route(
    agent: str,
    *,
    request_cloud: bool = False,
    cloud_enabled: bool = False,
    budget_ok: bool = False,
    reason: str | None = None,
    specialist_available: bool = False,
    deep_local_available: bool = False,
    local_web_attempted: bool = False,
    source_conflict_observed: bool = False,
    failure_evidence: bool = False,
    local_attempts: int = 0,
    human_approved: bool = False,
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
                agent,
                "local_specialist",
                route["local_specialist"],
                "specialist_available",
            )
        if deep_local_available and route.get("local_deep"):
            return RouteDecision(
                agent,
                "local_deep",
                route["local_deep"],
                "deep_local_available",
            )
        return RouteDecision(
            agent,
            "local_primary",
            route["local_primary"],
            "local_first",
        )

    if not cloud_enabled:
        raise PermissionError(
            "Escalade cloud demandée alors que le cloud est désactivé"
        )
    if not budget_ok:
        raise PermissionError("Escalade cloud refusée: budget non validé")
    if not reason:
        raise ValueError("Une raison explicite est obligatoire pour l'escalade cloud")

    triggers = escalation.get("triggers", {})
    if reason not in triggers:
        raise ValueError(f"Raison d'escalade inconnue: {reason}")

    trigger = triggers[reason]
    allowed_roles = set(trigger.get("allowed_roles", []))
    if allowed_roles and agent not in allowed_roles:
        raise PermissionError(
            f"Le rôle {agent} n'est pas autorisé pour le motif {reason}"
        )

    _enforce_trigger_conditions(
        trigger,
        local_web_attempted=local_web_attempted,
        source_conflict_observed=source_conflict_observed,
        failure_evidence=failure_evidence,
        local_attempts=local_attempts,
        human_approved=human_approved,
    )
    return RouteDecision(
        agent,
        "cloud_escalation",
        route["cloud_escalation"],
        reason,
    )
