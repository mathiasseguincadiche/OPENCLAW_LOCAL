from __future__ import annotations

import pytest

from clawlocal.routing import select_route


def test_local_is_default() -> None:
    decision = select_route("chef-operations")
    assert decision.route_kind == "local_primary"
    assert decision.model_alias == "qwen-general"


def test_specialist_must_be_explicitly_available() -> None:
    decision = select_route("ingenieur-devops", specialist_available=True)
    assert decision.route_kind == "local_specialist"
    assert decision.model_alias == "sera-devops"


def test_local_deep_is_explicit() -> None:
    decision = select_route("architecte-solutions", deep_local_available=True)
    assert decision.route_kind == "local_deep"
    assert decision.model_alias == "qwen-deep"


def test_cloud_is_denied_when_disabled_or_budget_not_validated() -> None:
    with pytest.raises(PermissionError):
        select_route("expert-recherche", request_cloud=True, cloud_enabled=False, budget_ok=True, reason="deep_web_research", local_web_attempted=True)
    with pytest.raises(PermissionError):
        select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=False, reason="deep_web_research", local_web_attempted=True)


def test_research_requires_local_web_before_cloud() -> None:
    with pytest.raises(PermissionError, match="tentative Web locale"):
        select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=True, reason="deep_web_research")
    decision = select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=True, reason="deep_web_research", local_web_attempted=True)
    assert decision.route_kind == "cloud_escalation"
    assert decision.model_alias == "research"


def test_source_conflict_requires_evidence() -> None:
    with pytest.raises(PermissionError, match="conflit de sources"):
        select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=True, reason="source_conflict")
    decision = select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=True, reason="source_conflict", source_conflict_observed=True)
    assert decision.route_kind == "cloud_escalation"


def test_old_web_freshness_reason_is_rejected() -> None:
    with pytest.raises(ValueError):
        select_route("expert-recherche", request_cloud=True, cloud_enabled=True, budget_ok=True, reason="web_freshness")
