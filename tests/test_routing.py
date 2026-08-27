from __future__ import annotations

import pytest

from clawlocal.routing import preferred_tier_for_phase, select_route


def test_unqualified_optional_model_falls_back_to_required_fast_model() -> None:
    decision = select_route("chef-operations")
    assert decision.route_kind == "local_primary"
    assert decision.model_alias == "qwen-general"
    assert decision.reason == "max_not_qualified"


def test_best_qualified_default_tier_is_selected_automatically() -> None:
    decision = select_route("chef-operations", qualified_models={"qwen-max"})
    assert decision.route_kind == "local_max"
    assert decision.model_alias == "qwen-max"


def test_specialist_must_be_explicitly_available_or_qualified() -> None:
    explicit = select_route("ingenieur-devops", specialist_available=True)
    assert explicit.route_kind == "local_specialist"
    assert explicit.model_alias == "devstral-devops"

    qualified = select_route(
        "ingenieur-devops",
        qualified_models={"devstral-devops"},
    )
    assert qualified.route_kind == "local_specialist"
    assert qualified.model_alias == "devstral-devops"


def test_local_deep_is_role_specific() -> None:
    decision = select_route("architecte-solutions", deep_local_available=True)
    assert decision.route_kind == "local_deep"
    assert decision.model_alias == "gemma-deep"


def test_local_max_is_explicit_and_uses_qwen38() -> None:
    decision = select_route("chef-operations", max_local_available=True)
    assert decision.route_kind == "local_max"
    assert decision.model_alias == "qwen-max"


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


def test_auditor_uses_different_family_when_producer_is_gemma() -> None:
    decision = select_route(
        "auditeur-qualite",
        producer_model_alias="gemma-review",
    )
    assert decision.route_kind == "local_independent"
    assert decision.model_alias == "qwen-general"


def test_auditor_can_use_qualified_qwen_max_as_independent_alternative() -> None:
    decision = select_route(
        "auditeur-qualite",
        qualified_models={"gemma-deep", "qwen-max"},
        producer_model_alias="gemma-review",
    )
    assert decision.route_kind == "local_independent"
    assert decision.model_alias == "qwen-max"


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
