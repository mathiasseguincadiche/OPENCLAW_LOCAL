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


_TIER_FIELDS = {
    "primary": "local_primary",
    "specialist": "local_specialist",
    "deep": "local_deep",
    "max": "local_max",
}


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


def _family(alias: str, catalog: dict[str, Any]) -> str | None:
    model = catalog.get("models", {}).get(alias)
    if not isinstance(model, dict):
        return None
    family = model.get("family")
    return str(family) if family else None


def _is_qualified(
    alias: str,
    catalog: dict[str, Any],
    qualified_models: set[str],
) -> bool:
    model = catalog["models"][alias]
    return bool(model.get("required")) or alias in qualified_models


def preferred_tier_for_phase(agent: str, phase: str) -> str:
    routing = load_contract("model_routing.yaml")
    route = routing.get("agents", {}).get(agent, {})
    tier = str(route.get("phase_preferences", {}).get(phase, "primary"))
    if tier not in _TIER_FIELDS:
        raise ValueError(f"tier local inconnu pour {agent}/{phase}: {tier}")
    return tier


def _select_local(
    agent: str,
    route: dict[str, Any],
    catalog: dict[str, Any],
    *,
    preferred_tier: str,
    qualified_models: set[str],
    explicit_tier: bool,
    producer_model_alias: str | None,
) -> RouteDecision:
    field = _TIER_FIELDS[preferred_tier]
    alias = route.get(field)
    fallback_reason: str | None = None

    if alias is None:
        fallback_reason = f"{preferred_tier}_not_configured"
    elif explicit_tier or _is_qualified(str(alias), catalog, qualified_models):
        selected = str(alias)
        route_kind = field
        if agent == "auditeur-qualite" and producer_model_alias:
            producer_family = _family(producer_model_alias, catalog)
            reviewer_family = _family(selected, catalog)
            if producer_family and producer_family == reviewer_family:
                independent = route.get("independent_alternative")
                if independent and _is_qualified(
                    str(independent), catalog, qualified_models
                ):
                    return RouteDecision(
                        agent,
                        "local_independent",
                        str(independent),
                        "reviewer_family_separated_from_producer",
                    )
                local_fallback = route.get("local_fallback")
                if (
                    local_fallback
                    and _family(str(local_fallback), catalog) != producer_family
                ):
                    return RouteDecision(
                        agent,
                        "local_independent",
                        str(local_fallback),
                        "reviewer_family_separated_from_producer",
                    )
        return RouteDecision(agent, route_kind, selected, f"preferred_{preferred_tier}")
    else:
        fallback_reason = f"{preferred_tier}_not_qualified"

    primary = str(route["local_primary"])
    if agent == "auditeur-qualite" and producer_model_alias:
        producer_family = _family(producer_model_alias, catalog)
        if producer_family and _family(primary, catalog) == producer_family:
            local_fallback = route.get("local_fallback")
            if local_fallback and _family(str(local_fallback), catalog) != producer_family:
                return RouteDecision(
                    agent,
                    "local_independent",
                    str(local_fallback),
                    "primary_family_matches_producer",
                )
    return RouteDecision(agent, "local_primary", primary, fallback_reason or "local_first")


def select_route(
    agent: str,
    *,
    request_cloud: bool = False,
    cloud_enabled: bool = False,
    budget_ok: bool = False,
    reason: str | None = None,
    specialist_available: bool = False,
    deep_local_available: bool = False,
    max_local_available: bool = False,
    preferred_tier: str | None = None,
    qualified_models: set[str] | None = None,
    producer_model_alias: str | None = None,
    local_web_attempted: bool = False,
    source_conflict_observed: bool = False,
    failure_evidence: bool = False,
    local_attempts: int = 0,
    human_approved: bool = False,
) -> RouteDecision:
    routing = load_contract("model_routing.yaml")
    catalog = load_contract("model_catalog.yaml")
    escalation = load_contract("escalation_policy.yaml")
    routes = routing["agents"]

    if agent not in routes:
        raise KeyError(f"Agent inconnu: {agent}")
    route = routes[agent]

    if not request_cloud:
        explicit = [
            ("specialist", specialist_available),
            ("deep", deep_local_available),
            ("max", max_local_available),
        ]
        selected_explicit = [tier for tier, enabled in explicit if enabled]
        if len(selected_explicit) > 1:
            raise ValueError("un seul tier local explicite peut être demandé")
        if preferred_tier is not None and preferred_tier not in _TIER_FIELDS:
            raise ValueError(f"tier local inconnu: {preferred_tier}")

        explicit_tier = bool(selected_explicit)
        tier = selected_explicit[0] if selected_explicit else str(
            preferred_tier or route.get("default_preferred_tier", "primary")
        )
        if tier not in _TIER_FIELDS:
            raise ValueError(f"tier local inconnu: {tier}")
        return _select_local(
            agent,
            route,
            catalog,
            preferred_tier=tier,
            qualified_models=set(qualified_models or set()),
            explicit_tier=explicit_tier,
            producer_model_alias=producer_model_alias,
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
