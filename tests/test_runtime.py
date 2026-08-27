from __future__ import annotations

import pytest

from clawlocal.runtime import (
    build_openclaw_agent_command,
    model_ref,
    route_request,
)


def test_model_ref_resolves_local_and_cloud_namespaces() -> None:
    assert model_ref("qwen-general") == "ollama/qwen3.5:9b"
    assert model_ref("gemma-review") == "ollama/gemma4"
    assert model_ref("research") == "openrouter/perplexity/sonar-pro-search"
    assert model_ref("frontier-reasoning") == "openrouter/openai/gpt-5.6-sol"


def test_local_route_is_default_and_command_targets_agent() -> None:
    decision, resolved = route_request("ingenieur-devops", cloud_enabled=False)
    assert decision.route_kind == "local_primary"
    assert resolved == "ollama/qwen3.5:9b"

    command = build_openclaw_agent_command(decision, resolved, "diagnostic")
    assert command[:5] == ["openclaw", "agent", "--agent", "ingenieur-devops", "--model"]
    assert command[5] == "ollama/qwen3.5:9b"
    assert command[-1] == "--json"


def test_cloud_route_requires_explicit_enable_and_reason() -> None:
    with pytest.raises(PermissionError):
        route_request(
            "expert-recherche",
            request_cloud=True,
            reason="web_freshness",
            cloud_enabled=False,
        )

    decision, resolved = route_request(
        "expert-recherche",
        request_cloud=True,
        reason="web_freshness",
        cloud_enabled=True,
    )
    assert decision.route_kind == "cloud_escalation"
    assert resolved == "openrouter/perplexity/sonar-pro-search"


def test_unsupported_custom_gguf_is_not_silently_executed() -> None:
    with pytest.raises(ValueError):
        model_ref("sera-devops")
