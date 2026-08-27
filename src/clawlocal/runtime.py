from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from clawlocal.config import load_contract
from clawlocal.routing import RouteDecision, select_route
from clawlocal.telemetry import try_record_route_event


def model_ref(model_alias: str) -> str:
    catalog = load_contract("model_catalog.yaml")
    if model_alias in catalog["models"]:
        model = catalog["models"][model_alias]
        provider = model["provider"]
        if provider == "ollama":
            return f"ollama/{model['runtime_id']}"
        if provider == "llama_cpp":
            return f"llamacpp/{model['runtime_id']}"
        raise ValueError(
            f"Le modèle local {model_alias} utilise {provider}; "
            "import/qualification explicite requis"
        )

    if model_alias in catalog["cloud_catalog"]:
        model = catalog["cloud_catalog"][model_alias]
        if model["provider"] != "openrouter":
            raise ValueError(f"Provider cloud non supporté: {model['provider']}")
        return f"openrouter/{model['runtime_id']}"

    raise KeyError(f"Alias modèle inconnu: {model_alias}")


def cloud_enabled_from_environment() -> bool:
    value = os.environ.get("OPENCLAW_LOCAL_CLOUD_ENABLED", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _backend_for_model(resolved_model: str) -> str:
    if resolved_model.startswith("ollama/"):
        platform = load_contract("platform.yaml")
        return str(platform.get("local_provider", {}).get("nominal_id", "ollama"))
    if resolved_model.startswith("llamacpp/"):
        return "llama-cpp"
    if resolved_model.startswith("openrouter/"):
        return "openrouter"
    return "unknown"


def route_request(
    agent: str,
    *,
    request_cloud: bool = False,
    reason: str | None = None,
    specialist_available: bool = False,
    deep_local_available: bool = False,
    cloud_enabled: bool | None = None,
    budget_ok: bool = False,
    local_web_attempted: bool = False,
    source_conflict_observed: bool = False,
    failure_evidence: bool = False,
    local_attempts: int = 0,
    human_approved: bool = False,
) -> tuple[RouteDecision, str]:
    enabled = (
        cloud_enabled_from_environment()
        if cloud_enabled is None
        else cloud_enabled
    )
    decision = select_route(
        agent,
        request_cloud=request_cloud,
        cloud_enabled=enabled,
        budget_ok=budget_ok,
        reason=reason,
        specialist_available=specialist_available,
        deep_local_available=deep_local_available,
        local_web_attempted=local_web_attempted,
        source_conflict_observed=source_conflict_observed,
        failure_evidence=failure_evidence,
        local_attempts=local_attempts,
        human_approved=human_approved,
    )
    resolved_model = model_ref(decision.model_alias)
    try_record_route_event(
        agent=decision.agent,
        model=resolved_model,
        route_kind=decision.route_kind,
        backend=_backend_for_model(resolved_model),
    )
    return decision, resolved_model


def build_openclaw_agent_command(
    decision: RouteDecision,
    resolved_model: str,
    message: str,
) -> list[str]:
    return [
        "openclaw",
        "agent",
        "--agent",
        decision.agent,
        "--model",
        resolved_model,
        "--message",
        message,
        "--json",
    ]


def route_evidence(
    decision: RouteDecision,
    resolved_model: str,
) -> dict[str, Any]:
    evidence = asdict(decision)
    evidence["resolved_model"] = resolved_model
    evidence["cloud"] = decision.route_kind == "cloud_escalation"
    return evidence
