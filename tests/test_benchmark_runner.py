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


def test_generation_payload_bounds_output_and_matches_nominal_keep_alive() -> None:
    payload = BENCHMARK.generation_payload(
        "qwen3.8:27b",
        "test",
        8192,
        0.1,
        256,
    )
    assert payload["stream"] is True
    assert payload["keep_alive"] == "15m"
    assert payload["options"]["num_ctx"] == 8192
    assert payload["options"]["num_predict"] == 256


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


def test_format_duration_is_operator_friendly() -> None:
    assert BENCHMARK.format_duration(9.6) == "10s"
    assert BENCHMARK.format_duration(65) == "1m05s"
    assert BENCHMARK.format_duration(3661) == "1h01m01s"
