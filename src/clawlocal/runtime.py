from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from clawlocal.config import load_contract
from clawlocal.routing import RouteDecision, select_route


def model_ref(model_alias: str) -> str:
    catalog = load_contract("model_catalog.yaml")
    models = catalog.get("models", {})
    if model_alias not in models:
        raise KeyError(f"Alias modèle local inconnu: {model_alias}")

    model = models[model_alias]
    provider = model["provider"]
    if provider == "ollama":
        return f"ollama/{model['runtime_id']}"
    if provider == "llama_cpp":
        return f"llamacpp/{model['runtime_id']}"
    raise ValueError(
        f"Le modèle local {model_alias} utilise {provider}; "
        "import/qualification explicite requis"
    )


def cloud_enabled_from_environment() -> bool:
    """Compatibility shim: Architecture V2 never enables cloud inference."""
    return False


def qualified_models_from_environment() -> set[str]:
    raw = os.environ.get("OPENCLAW_LOCAL_QUALIFIED_MODELS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def route_request(
    agent: str,
    *,
    request_cloud: bool = False,
    reason: str | None = None,
    specialist_available: bool = False,
    deep_local_available: bool = False,
    max_local_available: bool = False,
    preferred_tier: str | None = None,
    qualified_models: set[str] | None = None,
    producer_model_alias: str | None = None,
    cloud_enabled: bool | None = None,
    budget_ok: bool = False,
    local_web_attempted: bool = False,
    source_conflict_observed: bool = False,
    failure_evidence: bool = False,
    local_attempts: int = 0,
    human_approved: bool = False,
) -> tuple[RouteDecision, str]:
    """Resolve a request through the local-only V2 routing contract.

    Cloud-related keyword arguments are retained only to make older callers fail
    closed through ``select_route``; they can never enable an online model.
    """
    del cloud_enabled
    qualified = (
        qualified_models_from_environment()
        if qualified_models is None
        else set(qualified_models)
    )
    decision = select_route(
        agent,
        request_cloud=request_cloud,
        cloud_enabled=False,
        budget_ok=budget_ok,
        reason=reason,
        specialist_available=specialist_available,
        deep_local_available=deep_local_available,
        max_local_available=max_local_available,
        preferred_tier=preferred_tier,
        qualified_models=qualified,
        producer_model_alias=producer_model_alias,
        local_web_attempted=local_web_attempted,
        source_conflict_observed=source_conflict_observed,
        failure_evidence=failure_evidence,
        local_attempts=local_attempts,
        human_approved=human_approved,
    )
    return decision, model_ref(decision.model_alias)


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
    evidence["cloud"] = False
    evidence["local_only"] = True
    return evidence
