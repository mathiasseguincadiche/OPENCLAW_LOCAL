from __future__ import annotations

import pytest

from clawlocal.runtime import build_openclaw_agent_command, model_ref, route_request


def test_model_ref_resolves_local_and_cloud_namespaces() -> None:
    assert model_ref("qwen-general") == "ollama/qwen3.5:9b"
    assert model_ref("gemma-review") == "ollama/gemma4:12b"
    assert model_ref("gemma-deep") == "ollama/gemma4:26b"
    assert model_ref("devstral-devops") == "ollama/devstral-small-2:24b"
    assert model_ref("qwen-max") == "ollama/qwen3.8:27b"
    assert model_ref("research") == "openrouter/perplexity/sonar-pro-search"


def test_local_route_falls_back_to_fast_until_optional_model_is_qualified() -> None:
    decision, resolved = route_request(
        "ingenieur-devops",
        cloud_enabled=False,
        qualified_models=set(),
    )
    assert decision.route_kind == "local_primary"
    assert resolved == "ollama/qwen3.5:9b"
    command = build_openclaw_agent_command(decision, resolved, "diagnostic")
    assert command[:5] == [
        "openclaw",
        "agent",
        "--agent",
        "ingenieur-devops",
        "--model",
    ]
    assert command[5] == "ollama/qwen3.5:9b"
    assert command[-1] == "--json"


def test_qualified_specialist_becomes_default_for_devops() -> None:
    decision, resolved = route_request(
        "ingenieur-devops",
        cloud_enabled=False,
        qualified_models={"devstral-devops"},
    )
    assert decision.route_kind == "local_specialist"
    assert resolved == "ollama/devstral-small-2:24b"


def test_qualified_qwen_max_becomes_default_for_operations() -> None:
    decision, resolved = route_request(
        "chef-operations",
        cloud_enabled=False,
        qualified_models={"qwen-max"},
    )
    assert decision.route_kind == "local_max"
    assert resolved == "ollama/qwen3.8:27b"


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


def test_unsupported_custom_gguf_is_not_silently_executed() -> None:
    with pytest.raises(ValueError):
        model_ref("sera-devops")
