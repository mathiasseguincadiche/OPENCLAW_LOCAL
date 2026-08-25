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


def test_cloud_is_denied_when_disabled() -> None:
    with pytest.raises(PermissionError):
        select_route(
            "expert-recherche",
            request_cloud=True,
            cloud_enabled=False,
            reason="web_freshness",
        )


def test_research_can_escalate_for_freshness() -> None:
    decision = select_route(
        "expert-recherche",
        request_cloud=True,
        cloud_enabled=True,
        reason="web_freshness",
    )
    assert decision.route_kind == "cloud_escalation"
    assert decision.model_alias == "research"


def test_unknown_reason_is_rejected() -> None:
    with pytest.raises(ValueError):
        select_route(
            "chef-operations",
            request_cloud=True,
            cloud_enabled=True,
            reason="convenience",
        )
