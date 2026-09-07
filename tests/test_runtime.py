from __future__ import annotations

import pytest

from clawlocal.runtime import (
    build_openclaw_agent_command,
    cloud_enabled_from_environment,
    model_ref,
    route_request,
)


def test_model_ref_resolves_only_supported_local_v2_models() -> None:
    assert model_ref("qwen-max") == "ollama/qwen3.5:9b-q4_K_M"
    assert model_ref("gemma-deep") == "ollama/gemma4:12b-it-q4_K_M"
    assert (
        model_ref("devstral-devops")
        == "ollama/hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M"
    )
    for alias in ("research", "frontier-reasoning", "frontier-review"):
        with pytest.raises(KeyError):
            model_ref(alias)


def test_removed_small_legacy_and_cloud_aliases_are_not_supported() -> None:
    for alias in (
        "qwen-general",
        "gemma-review",
        "sera-devops",
        "research",
        "frontier-reasoning",
        "frontier-review",
    ):
        with pytest.raises(KeyError):
            model_ref(alias)


def test_devops_nominal_route_is_ministral_reasoning_compat_alias() -> None:
    decision, resolved = route_request(
        "ingenieur-devops",
        cloud_enabled=False,
        qualified_models=set(),
    )
    assert decision.model_alias == "devstral-devops"
    assert (
        resolved
        == "ollama/hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M"
    )
    command = build_openclaw_agent_command(decision, resolved, "diagnostic")
    assert command[:5] == [
        "openclaw",
        "agent",
        "--agent",
        "ingenieur-devops",
        "--model",
    ]
    assert command[5] == resolved
    assert command[-1] == "--json"


def test_operations_nominal_route_is_qwen35() -> None:
    decision, resolved = route_request(
        "chef-operations",
        qualified_models=set(),
    )
    assert decision.model_alias == "qwen-max"
    assert resolved == "ollama/qwen3.5:9b-q4_K_M"


def test_architecture_nominal_route_is_gemma4_12b() -> None:
    decision, resolved = route_request(
        "architecte-solutions",
        qualified_models=set(),
    )
    assert decision.model_alias == "gemma-deep"
    assert resolved == "ollama/gemma4:12b-it-q4_K_M"


def test_cloud_cannot_be_enabled_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENCLAW_LOCAL_CLOUD_ENABLED", "true")
    assert cloud_enabled_from_environment() is False


def test_cloud_route_is_always_rejected_even_with_legacy_preconditions() -> None:
    with pytest.raises(PermissionError, match="local-only"):
        route_request(
            "expert-recherche",
            request_cloud=True,
            reason="deep_web_research",
            cloud_enabled=True,
            budget_ok=True,
            local_web_attempted=True,
            source_conflict_observed=True,
            failure_evidence=True,
            local_attempts=10,
            human_approved=True,
        )
