from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "52_compare_tool_calling_models.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("model_challenger_under_test", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHALLENGER = load_module()


def load_yaml(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_active_fleet_stays_exactly_three_models() -> None:
    catalog = load_yaml(ROOT / "config" / "v1" / "model_catalog.yaml")
    models = catalog["models"]
    assert isinstance(models, dict)
    assert set(models) == {"qwen-max", "gemma-deep", "devstral-devops"}


def test_ministral_is_mandatory_benchmark_challenger_not_routed_model() -> None:
    catalog = load_yaml(ROOT / "config" / "v1" / "model_catalog.yaml")
    challengers = catalog["benchmark_challengers"]
    assert isinstance(challengers, dict)
    model = challengers["ministral-tool-calling"]
    assert isinstance(model, dict)
    assert model["runtime_id"] == "ministral-3:14b-instruct-2512-q4_K_M"
    assert model["quantization"] == "Q4_K_M"
    assert model["required_for_selection"] is True
    assert model["routing_active"] is False
    assert model["incumbent_alias"] == "gemma-deep"
    assert model["automatic_promotion"] is False


def test_policy_requires_native_tool_calling_comparison_and_human_decision() -> None:
    policy = load_yaml(ROOT / "config" / "v1" / "qualification_policy.yaml")
    gate = policy["model_selection_challenger"]
    assert isinstance(gate, dict)
    assert gate["required_before_manual_model_selection"] is True
    assert gate["incumbent_alias"] == "gemma-deep"
    assert gate["challenger_alias"] == "ministral-tool-calling"
    assert gate["protocol"] == "native_tool_calling_v1"
    assert gate["required_capabilities"] == [
        "native_tool_calling",
        "tool_feedback_repair",
    ]
    assert gate["automatic_promotion"] is False
    assert gate["human_decision_required"] is True


def test_tool_call_matching_is_strict_but_path_separator_tolerant() -> None:
    calls = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": {"path": "config\\prod.yaml"},
            },
        }
    ]
    assert CHALLENGER.has_tool_call(
        calls,
        name="read_file",
        argument="path",
        expected="config/prod.yaml",
    )
    assert not CHALLENGER.has_tool_call(
        calls,
        name="list_files",
        argument="directory",
        expected="config",
    )


def test_response_fingerprint_keeps_no_raw_content() -> None:
    response = {
        "message": {
            "content": "sensitive output",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "list_files",
                        "arguments": {"directory": "config"},
                    },
                }
            ],
        },
        "eval_count": 20,
        "eval_duration": 2_000_000_000,
    }
    fingerprint = CHALLENGER.response_fingerprint(response)
    assert "sensitive output" not in str(fingerprint)
    assert fingerprint["content_chars"] == len("sensitive output")
    assert fingerprint["tokens_per_second"] == 10.0
    assert fingerprint["tool_calls"] == [
        {"name": "list_files", "arguments": {"directory": "config"}}
    ]
