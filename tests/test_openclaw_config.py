import json
from pathlib import Path
from typing import Any

import pytest

from clawlocal.openclaw_config import build_openclaw_patch

EXPECTED_AGENTS = {
    "chef-operations",
    "expert-recherche",
    "architecte-solutions",
    "ingenieur-devops",
    "ingenieur-securite",
    "ingenieur-release-forges",
    "redacteur-technique",
    "auditeur-qualite",
}

EXPECTED_MODELS = {
    "qwen3.8:27b",
    "gemma4:26b",
    "devstral-small-2:24b",
}
EXPECTED_SYCL_MODELS = {
    "qwen3.8:27B",
    "gemma4:26B",
    "devstral-small-2:24B",
}

PINNED_OPENCLAW_VERSION = "2026.7.1-2"
PINNED_MODEL_KEYS = {
    "id",
    "name",
    "api",
    "baseUrl",
    "reasoning",
    "input",
    "cost",
    "contextWindow",
    "contextTokens",
    "maxTokens",
    "thinkingLevelMap",
    "params",
    "agentRuntime",
    "headers",
    "compat",
    "mediaInput",
    "metadataSource",
}


def _entries_by_id(patch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = patch["agents"]["list"]
    return {str(entry["id"]): entry for entry in entries}


def test_patch_materializes_all_agents_without_cloud_fallback() -> None:
    patch = build_openclaw_patch(Path("E:/AI/OpenClawLocal"))
    entries = _entries_by_id(patch)
    assert set(entries) == EXPECTED_AGENTS
    assert patch["gateway"] == {"mode": "local", "bind": "loopback"}
    assert patch["agents"]["defaults"]["skipBootstrap"] is True
    assert [entry["id"] for entry in patch["agents"]["list"] if entry.get("default")] == [
        "chef-operations"
    ]
    for agent_id, entry in entries.items():
        assert entry["workspace"].replace("\\", "/").endswith(
            f"workspaces/{agent_id}"
        )
        assert entry["model"]["primary"].startswith("ollama/")
        assert all(
            model.startswith("ollama/")
            for model in entry["model"]["fallbacks"]
        )
        assert "openrouter/" not in str(entry["model"])
        assert entry["tools"]["fs"]["workspaceOnly"] is True
        assert entry["tools"]["exec"]["mode"] == "ask"
        assert entry["tools"]["elevated"]["enabled"] is False


def test_research_agent_gets_browser_and_local_web_is_configured() -> None:
    patch = build_openclaw_patch(Path("C:/OpenClawLocal"))
    research_tools = _entries_by_id(patch)["expert-recherche"]["tools"]
    assert "browser" in research_tools["alsoAllow"]
    web = patch["tools"]["web"]
    assert web["search"]["enabled"] is True
    assert web["search"]["provider"] == "parallel-free"
    assert web["fetch"]["enabled"] is True


def test_read_only_roles_cannot_mutate_or_exec() -> None:
    entries = _entries_by_id(build_openclaw_patch(Path("C:/OpenClawLocal")))
    review_roles = (
        "chef-operations",
        "expert-recherche",
        "architecte-solutions",
        "auditeur-qualite",
    )
    for agent_id in review_roles:
        denied = set(entries[agent_id]["tools"]["deny"])
        assert {"write", "edit", "apply_patch", "exec", "process"} <= denied


def test_provider_exposes_exactly_three_performance_models() -> None:
    patch = build_openclaw_patch(Path("C:/OpenClawLocal"))
    provider = patch["models"]["providers"]["ollama"]
    assert provider["api"] == "ollama"
    ids = {model["id"] for model in provider["models"]}
    assert ids == EXPECTED_MODELS
    assert all(model["input"] == ["text", "image"] for model in provider["models"])
    assert all(model["contextTokens"] == 16384 for model in provider["models"])
    assert all("metadata" not in model for model in provider["models"])


def test_multimodal_defaults_use_qwen38_then_gemma26() -> None:
    defaults = build_openclaw_patch(Path("C:/OpenClawLocal"))["agents"]["defaults"]
    expected = {
        "primary": "ollama/qwen3.8:27b",
        "fallbacks": ["ollama/gemma4:26b"],
    }
    assert defaults["model"] == expected
    assert defaults["imageModel"] == expected
    assert defaults["pdfModel"] == expected


def test_intel_sycl_backend_routes_text_but_keeps_multimodal_on_ollama() -> None:
    patch = build_openclaw_patch(
        Path("C:/OpenClawLocal"), backend_id="llama-cpp-sycl"
    )
    providers = patch["models"]["providers"]
    assert set(providers) == {"ollama", "intel-sycl"}

    sycl = providers["intel-sycl"]
    assert sycl["baseUrl"] == "http://127.0.0.1:8080/v1"
    assert sycl["api"] == "openai-completions"
    assert sycl["apiKey"] == "intel-sycl-local"
    assert {model["id"] for model in sycl["models"]} == EXPECTED_SYCL_MODELS
    assert all(model["input"] == ["text"] for model in sycl["models"])
    assert all(model["contextWindow"] == 8192 for model in sycl["models"])
    assert all(model["compat"]["toolSchemaProfile"] == "llamacpp" for model in sycl["models"])

    entries = _entries_by_id(patch)
    for entry in entries.values():
        assert entry["model"]["primary"].startswith("intel-sycl/")
        assert all(
            fallback.startswith("intel-sycl/")
            for fallback in entry["model"]["fallbacks"]
        )

    defaults = patch["agents"]["defaults"]
    assert defaults["model"] == {
        "primary": "intel-sycl/qwen3.8:27B",
        "fallbacks": ["intel-sycl/gemma4:26B"],
    }
    expected_multimodal = {
        "primary": "ollama/qwen3.8:27b",
        "fallbacks": ["ollama/gemma4:26b"],
    }
    assert defaults["imageModel"] == expected_multimodal
    assert defaults["pdfModel"] == expected_multimodal


def test_unknown_backend_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="Backend OpenClaw invalide"):
        build_openclaw_patch(Path("C:/OpenClawLocal"), backend_id="unknown")


def test_patch_matches_pinned_openclaw_schema_surface() -> None:
    runtime_lock = json.loads(
        Path("config/v1/runtime_versions.json").read_text(encoding="utf-8")
    )
    assert runtime_lock["openclaw"]["preferred"] == PINNED_OPENCLAW_VERSION

    patch = build_openclaw_patch(Path("C:/OpenClawLocal"))
    agents = patch["agents"]
    assert set(agents) == {"defaults", "list"}
    assert "ownership" not in agents
    assert "entries" not in agents
    assert isinstance(agents["list"], list)
    assert len(agents["list"]) == 8
    assert len({entry["id"] for entry in agents["list"]}) == 8

    models = patch["models"]["providers"]["ollama"]["models"]
    for model in models:
        assert set(model) <= PINNED_MODEL_KEYS
        assert "metadata" not in model
