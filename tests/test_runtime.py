from __future__ import annotations

import pytest

from clawlocal.runtime import build_openclaw_agent_command, model_ref, route_request


def test_model_ref_resolves_supported_local_and_cloud_namespaces() -> None:
    assert model_ref("qwen-max") == "ollama/qwen3.8:27b"
    assert model_ref("gemma-deep") == "ollama/gemma4:26b"
    assert model_ref("devstral-devops") == "ollama/devstral-small-2:24b"
    assert model_ref("research") == "openrouter/perplexity/sonar-pro-search"


def test_removed_small_and_legacy_aliases_are_not_supported() -> None:
    for alias in ("qwen-general", "gemma-review", "sera-devops"):
        with pytest.raises(KeyError):
            model_ref(alias)


def test_devops_nominal_route_is_devstral() -> None:
    decision, resolved = route_request(
        "ingenieur-devops",
        cloud_enabled=False,
        qualified_models=set(),
    )
    assert decision.model_alias == "devstral-devops"
    assert resolved == "ollama/devstral-small-2:24b"
    command = build_openclaw_agent_command(decision, resolved, "diagnostic")
    assert command[:5] == [
        "openclaw",
        "agent",
        "--agent",
        "ingenieur-devops",
        "--model",
    ]
    assert command[5] == "ollama/devstral-small-2:24b"
    assert command[-1] == "--json"


def test_operations_nominal_route_is_qwen38() -> None:
    decision, resolved = route_request(
        "chef-operations",
        cloud_enabled=False,
        qualified_models=set(),
    )
    assert decision.model_alias == "qwen-max"
    assert resolved == "ollama/qwen3.8:27b"


def test_architecture_nominal_route_is_gemma26() -> None:
    decision, resolved = route_request(
        "architecte-solutions",
        cloud_enabled=False,
        qualified_models=set(),
    )
    assert decision.model_alias == "gemma-deep"
    assert resolved == "ollama/gemma4:26b"


def test_cloud_route_requires_enable_budget_reason_and_precondition() -> None:
    with pytest.raises(PermissionError):
        route_request(
            "expert-recherche",
            request_cloud=True,
            reason="deep_web_research",
            cloud_enabled=False,
            budget_ok=True,
            local_web_attempted=True,
        )
    decision, resolved = route_request(
        "expert-recherche",
        request_cloud=True,
        reason="deep_web_research",
        cloud_enabled=True,
        budget_ok=True,
        local_web_attempted=True,
    )
    assert decision.route_kind == "cloud_escalation"
    assert resolved == "openrouter/perplexity/sonar-pro-search"
