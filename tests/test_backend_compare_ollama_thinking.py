from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "28_compare_local_backends.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("backend_compare_ollama_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ollama_benchmark_disables_thinking_and_unloads_every_model() -> None:
    module = load_module()
    captured: list[dict[str, Any]] = []

    def fake_post_json(
        url: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        captured.append({"url": url, "payload": payload, "timeout": timeout})
        if not payload.get("messages"):
            return {
                "message": {"content": "", "thinking": ""},
                "done_reason": "unload",
            }
        return {
            "message": {"content": "ok", "thinking": ""},
            "load_duration": 1_000_000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 1_000_000_000,
            "eval_count": 5,
            "eval_duration": 1_000_000_000,
            "done_reason": "stop",
        }

    def fake_get_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
        assert url.endswith("/api/ps")
        assert timeout == 10
        return {"models": []}

    module.post_json = fake_post_json
    module.get_json = fake_get_json
    for model in ("qwen3.8:27b", "gemma4:26b", "devstral-small-2:24b"):
        result = module.run_ollama(
            "http://127.0.0.1:11434", model, "test", 32, 10.0
        )
        assert result["content"] == "ok"
        assert result["unloaded_after_case"] is True

    generation_calls = [
        item for item in captured if bool(item["payload"].get("messages"))
    ]
    unload_calls = [
        item for item in captured if not item["payload"].get("messages")
    ]
    assert len(generation_calls) == 3
    assert len(unload_calls) == 6
    assert all(item["payload"]["think"] is False for item in generation_calls)
    assert all(item["payload"]["options"]["num_ctx"] == 8192 for item in generation_calls)
    assert all(item["payload"]["keep_alive"] == 0 for item in generation_calls)
    assert all(item["payload"]["keep_alive"] == 0 for item in unload_calls)
