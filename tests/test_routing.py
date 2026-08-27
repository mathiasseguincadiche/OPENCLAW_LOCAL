from __future__ import annotations

import pytest

from clawlocal.routing import preferred_tier_for_phase, select_route


def test_performance_models_are_nominal_without_small_fallbacks() -> None:
    assert select_route("chef-operations").model_alias == "qwen-max"
    assert select_route("expert-recherche").model_alias == "qwen-max"
    assert select_route("architecte-solutions").model_alias == "gemma-deep"
    assert select_route("ingenieur-devops").model_alias == "devstral-devops"
    assert select_route("ingenieur-securite").model_alias == "qwen-max"
    assert select_route("ingenieur-release-forges").model_alias == "qwen-max"
    assert select_route("redacteur-technique").model_alias == "gemma-deep"
    assert select_route("auditeur-qualite").model_alias == "gemma-deep"


def test_specialist_deep_and_max_tiers_use_only_supported_models() -> None:
    specialist = select_route("ingenieur-devops", specialist_available=True)
    assert specialist.route_kind == "local_specialist"
    assert specialist.model_alias == "devstral-devops"

    deep = select_route("architecte-solutions", deep_local_available=True)
    assert deep.route_kind == "local_deep"
    assert deep.model_alias == "gemma-deep"

    maximum = select_route("chef-operations", max_local_available=True)
    assert maximum.route_kind == "local_max"
    assert maximum.model_alias == "qwen-max"


def test_only_one_explicit_local_tier_can_be_requested() -> None:
    with pytest.raises(ValueError, match="un seul tier"):
        select_route(
            "ingenieur-devops",
            specialist_available=True,
            max_local_available=True,
        )


def test_phase_preferences_are_contractual() -> None:
    assert preferred_tier_for_phase("chef-operations", "plan") == "max"
    assert preferred_tier_for_phase("ingenieur-devops", "execute") == "specialist"
    assert preferred_tier_for_phase("auditeur-qualite", "review") == "deep"


def test_auditor_uses_qwen_when_producer_is_gemma() -> None:
    decision = select_route(
        "auditeur-qualite",
        producer_model_alias="gemma-deep",
    )
    assert decision.route_kind == "local_independent"
    assert decision.model_alias == "qwen-max"


def test_auditor_keeps_gemma_when_producer_is_qwen() -> None:
    decision = select_route(
        "auditeur-qualite",
        producer_model_alias="qwen-max",
    )
    assert decision.model_alias == "gemma-deep"


def test_cloud_is_denied_when_disabled_or_budget_not_validated() -> None:
    with pytest.raises(PermissionError):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=False,
            budget_ok=True,
            reason="deep_web_research",
            local_web_attempted=True,
        )
    with pytest.raises(PermissionError):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=True,
            budget_ok=False,
            reason="deep_web_research",
            local_web_attempted=True,
        )


def test_research_requires_local_web_before_cloud() -> None:
    with pytest.raises(PermissionError, match="tentative Web locale"):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=True,
            budget_ok=True,
            reason="deep_web_research",
        )
    decision = select_route(
        "expert-recherche",
        request_cloud=True,
        cloud_enabled=True,
        budget_ok=True,
        reason="deep_web_research",
        local_web_attempted=True,
    )
    assert decision.route_kind == "cloud_escalation"
    assert decision.model_alias == "research"


def test_source_conflict_requires_evidence() -> None:
    with pytest.raises(PermissionError, match="conflit de sources"):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=True,
            budget_ok=True,
            reason="source_conflict",
        )
    decision = select_route(
        "expert-recherche",
        request_cloud=True,
        cloud_enabled=True,
        budget_ok=True,
        reason="source_conflict",
        source_conflict_observed=True,
    )
    assert decision.route_kind == "cloud_escalation"


def test_old_web_freshness_reason_is_rejected() -> None:
    with pytest.raises(ValueError):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=True,
            budget_ok=True,
            reason="web_freshness",
        )
