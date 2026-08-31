from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "28_compare_local_backends.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("backend_compare", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sycl_router_base_strips_openai_v1_suffix() -> None:
    module = _load_module()
    assert module._sycl_router_base("http://127.0.0.1:8080/v1") == (
        "http://127.0.0.1:8080"
    )


def test_unload_sycl_model_uses_router_endpoint_and_waits_for_unloaded(
    monkeypatch: Any,
) -> None:
    module = _load_module()
    calls: list[tuple[str, str]] = []

    def fake_post(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        calls.append(("post", url))
        assert payload == {"model": "qwen3.8:27B"}
        assert timeout == 30.0
        return {"success": True}

    def fake_get(url: str, timeout: float = 5.0) -> dict[str, Any]:
        calls.append(("get", url))
        assert timeout == 10
        return {
            "data": [
                {
                    "id": "qwen3.8:27B",
                    "status": {"value": "unloaded"},
                }
            ]
        }

    monkeypatch.setattr(module, "post_json", fake_post)
    monkeypatch.setattr(module, "get_json", fake_get)
    module.unload_sycl_model(
        "http://127.0.0.1:8080/v1",
        "qwen3.8:27B",
        timeout=90.0,
    )

    assert calls == [
        ("post", "http://127.0.0.1:8080/models/unload"),
        ("get", "http://127.0.0.1:8080/models?reload=1"),
    ]
