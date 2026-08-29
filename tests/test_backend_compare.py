from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "28_compare_local_backends.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("backend_compare_under_test", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPARE = load_module()


def test_required_models_are_exactly_the_supported_fleet() -> None:
    assert set(COMPARE.required_models()) == {
        "qwen3.8:27b",
        "gemma4:26b",
        "devstral-small-2:24b",
    }


def test_rate_uses_nanosecond_durations() -> None:
    assert COMPARE._rate(20, 1_000_000_000) == 20.0
    assert COMPARE._rate(0, 1_000_000_000) is None
    assert COMPARE._rate(20, 0) is None


def test_summary_never_authorizes_backend_promotion() -> None:
    models = ["model-a"]
    cases = [
        {
            "backend": "ollama-vulkan",
            "model": "model-a",
            "status": "ok",
            "wall_ms": 1000.0,
            "tokens_per_second": 10.0,
            "prompt_tokens_per_second": 100.0,
        },
        {
            "backend": "llama-cpp-sycl",
            "model": "model-a",
            "status": "ok",
            "wall_ms": 800.0,
            "tokens_per_second": 20.0,
            "prompt_tokens_per_second": 150.0,
        },
    ]
    report = COMPARE.summarize(cases, models)
    assert report["complete"] is True
    assert report["promotion_allowed"] is False
    assert report["models"]["model-a"]["sycl_decode_speedup_vs_ollama"] == 2.0


def test_summary_fails_completeness_when_one_backend_errors() -> None:
    models = ["model-a"]
    cases = [
        {
            "backend": "ollama-vulkan",
            "model": "model-a",
            "status": "ok",
            "wall_ms": 1000.0,
            "tokens_per_second": 10.0,
            "prompt_tokens_per_second": 100.0,
        },
        {
            "backend": "llama-cpp-sycl",
            "model": "model-a",
            "status": "error",
            "error": "boom",
        },
    ]
    report = COMPARE.summarize(cases, models)
    assert report["complete"] is False
    assert report["errors"] == 1
    assert report["promotion_allowed"] is False
