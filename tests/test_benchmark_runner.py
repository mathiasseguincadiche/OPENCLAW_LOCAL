from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_local.py"


def load_benchmark_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("benchmark_local_under_test", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BENCHMARK = load_benchmark_module()


def test_generation_payload_bounds_output_and_matches_chat_contract() -> None:
    payload = BENCHMARK.generation_payload(
        "qwen3.8:27b",
        "test",
        8192,
        0.1,
        256,
    )
    assert payload["stream"] is True
    assert payload["keep_alive"] == "15m"
    assert payload["messages"] == [{"role": "user", "content": "test"}]
    assert "prompt" not in payload
    assert payload["options"]["num_ctx"] == 8192
    assert payload["options"]["num_predict"] == 256
    assert "think" not in payload


def test_generation_payload_can_explicitly_disable_thinking() -> None:
    payload = BENCHMARK.generation_payload(
        "qwen3.8:27b",
        "test",
        8192,
        0.1,
        256,
        False,
    )
    assert payload["think"] is False


def test_qwen_quick_mode_disables_thinking_and_keeps_scenario_limit() -> None:
    model = {"family": "qwen"}
    limit, think, mode = BENCHMARK.resolve_generation_policy(model, 192, "off")
    assert limit == 192
    assert think is False
    assert mode == "off"


def test_qwen_native_mode_is_bounded_to_768_without_disabling_thinking() -> None:
    model = {"family": "qwen"}
    limit, think, mode = BENCHMARK.resolve_generation_policy(model, 192, "native")
    assert limit == BENCHMARK.QWEN_NATIVE_MAX_OUTPUT_TOKENS == 768
    assert think is None
    assert mode == "native"


def test_gemma_disables_thinking_for_bounded_functional_gates() -> None:
    model = {"family": "gemma"}
    limit, think, mode = BENCHMARK.resolve_generation_policy(model, 320, "native")
    assert limit == 320
    assert think is False
    assert mode == "off"


def test_non_reasoning_models_keep_scenario_limit_and_native_behavior() -> None:
    model = {"family": "mistral"}
    limit, think, mode = BENCHMARK.resolve_generation_policy(model, 320, "off")
    assert limit == 320
    assert think is None
    assert mode == "not_applicable"


def test_scenario_output_limit_supports_default_and_override() -> None:
    suite = {"default_max_output_tokens": 512}
    assert BENCHMARK.scenario_output_limit({"id": "default"}, suite) == 512
    assert (
        BENCHMARK.scenario_output_limit(
            {"id": "override", "max_output_tokens": 128},
            suite,
        )
        == 128
    )


@pytest.mark.parametrize("value", [0, -1, 2049, "invalid"])
def test_scenario_output_limit_rejects_unsafe_values(value: object) -> None:
    with pytest.raises(ValueError):
        BENCHMARK.scenario_output_limit(
            {"id": "bad", "max_output_tokens": value},
            {},
        )


def test_versioned_suite_has_safe_output_limits() -> None:
    suite = BENCHMARK.load_yaml(ROOT / "benchmarks" / "suites" / "devops_v2.yaml")
    scenarios = list(suite["scenarios"])
    assert len(scenarios) == 12
    for scenario in scenarios:
        limit = BENCHMARK.scenario_output_limit(scenario, suite)
        assert 1 <= limit <= BENCHMARK.MAX_CONFIGURED_OUTPUT_TOKENS


def test_full_matrix_keeps_all_8k_and_only_four_targeted_16k_scenarios() -> None:
    suite = BENCHMARK.load_yaml(ROOT / "benchmarks" / "suites" / "devops_v2.yaml")
    policy = BENCHMARK.load_yaml(ROOT / "config" / "v1" / "qualification_policy.yaml")
    scenarios = list(suite["scenarios"])
    enabled_8k = [
        scenario
        for scenario in scenarios
        if BENCHMARK.scenario_enabled_for_context(scenario, 8192, policy)
    ]
    enabled_16k = [
        scenario
        for scenario in scenarios
        if BENCHMARK.scenario_enabled_for_context(scenario, 16384, policy)
    ]
    assert len(enabled_8k) == 12
    assert [str(item["id"]) for item in enabled_16k] == [
        "project-intake-analysis",
        "kubernetes-root-cause",
        "tool-feedback-repair-json",
        "long-context-discipline",
    ]
    assert 3 * (len(enabled_8k) + len(enabled_16k)) == 48


def test_format_duration_is_operator_friendly() -> None:
    assert BENCHMARK.format_duration(9.6) == "10s"
    assert BENCHMARK.format_duration(65) == "1m05s"
    assert BENCHMARK.format_duration(3661) == "1h01m01s"
