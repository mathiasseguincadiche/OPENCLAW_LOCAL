from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_backend_compare() -> ModuleType:
    path = ROOT / "scripts" / "28_compare_local_backends.py"
    spec = importlib.util.spec_from_file_location("backend_compare_reasoning_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_powershell_sycl_smoke_disables_thinking_deterministically() -> None:
    helper = (
        ROOT / "scripts" / "windows" / "lib" / "intel_sycl_smoke.ps1"
    ).read_text(encoding="utf-8")
    assert "Invoke-IntelSyclDeterministicSmoke" in helper
    assert "enable_thinking = $false" in helper
    assert "reasoning_content" in helper
    assert "LOCAL_OK" in helper

    setup = (ROOT / "scripts" / "windows" / "12_setup_intel_sycl.ps1").read_text(
        encoding="utf-8"
    )
    verify = (ROOT / "scripts" / "windows" / "14_verify_intel_sycl.ps1").read_text(
        encoding="utf-8"
    )
    for script in (setup, verify):
        assert "intel_sycl_smoke.ps1" in script
        assert "Invoke-IntelSyclDeterministicSmoke" in script


def test_sycl_benchmark_disables_thinking_for_backend_comparability() -> None:
    module = _load_backend_compare()
    captured: dict[str, Any] = {}
    unload_calls: list[tuple[str, str]] = []

    def fake_post_json(
        url: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {
            "choices": [
                {
                    "message": {"content": "ok", "reasoning_content": ""},
                    "finish_reason": "stop",
                }
            ],
            "timings": {
                "prompt_n": 5,
                "predicted_n": 2,
                "prompt_per_second": 10.0,
                "predicted_per_second": 5.0,
            },
        }

    def fake_unload_sycl_model(
        endpoint: str,
        model: str,
        *,
        timeout: float = 90.0,
    ) -> None:
        assert timeout == 90.0
        unload_calls.append((endpoint, model))

    module.post_json = fake_post_json
    module.unload_sycl_model = fake_unload_sycl_model
    result = module.run_sycl(
        "http://127.0.0.1:8080/v1",
        "qwen3.5:9b-q4_K_M",
        "test",
        32,
        10.0,
    )

    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["payload"]["chat_template_kwargs"] == {
        "enable_thinking": False
    }
    assert unload_calls == [
        ("http://127.0.0.1:8080/v1", "qwen3.5:9b-q4_K_M")
    ]
    assert result["content"] == "ok"
    assert result["reasoning_content_present"] is False
    assert result["unloaded_after_case"] is True
