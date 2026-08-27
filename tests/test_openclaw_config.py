from pathlib import Path

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


def test_patch_materializes_all_agents_without_cloud_fallback() -> None:
    patch = build_openclaw_patch(Path("E:/AI/OpenClawLocal"))
    entries = patch["agents"]["entries"]
    assert set(entries) == EXPECTED_AGENTS
    assert patch["gateway"] == {"mode": "local", "bind": "loopback"}
    assert patch["agents"]["defaults"]["skipBootstrap"] is True
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
    research_tools = patch["agents"]["entries"]["expert-recherche"]["tools"]
    assert "browser" in research_tools["alsoAllow"]
    web = patch["tools"]["web"]
    assert web["search"]["enabled"] is True
    assert web["search"]["provider"] == "parallel-free"
    assert web["fetch"]["enabled"] is True


def test_read_only_roles_cannot_mutate_or_exec() -> None:
    entries = build_openclaw_patch(Path("C:/OpenClawLocal"))["agents"]["entries"]
    review_roles = (
        "chef-operations",
        "expert-recherche",
        "architecte-solutions",
        "auditeur-qualite",
    )
    for agent_id in review_roles:
        denied = set(entries[agent_id]["tools"]["deny"])
        assert {"write", "edit", "apply_patch", "exec", "process"} <= denied


def test_provider_uses_explicit_models_and_multimodal_metadata() -> None:
    patch = build_openclaw_patch(Path("C:/OpenClawLocal"))
    provider = patch["models"]["providers"]["ollama"]
    assert provider["api"] == "ollama"
    ids = {model["id"] for model in provider["models"]}
    assert {
        "qwen3.5:9b",
        "gemma4:12b",
        "gemma4:26b",
        "devstral-small-2:24b",
        "qwen3.8:27b",
    } <= ids
    gemma = next(
        model for model in provider["models"] if model["id"] == "gemma4:12b"
    )
    assert gemma["input"] == ["text", "image"]
    assert gemma["contextTokens"] == 16384
