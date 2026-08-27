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
        assert entry["workspace"].replace("\\", "/").endswith(f"workspaces/{agent_id}")
        assert entry["model"]["primary"].startswith("ollama/")
        assert all(model.startswith("ollama/") for model in entry["model"]["fallbacks"])
        assert "openrouter/" not in str(entry["model"])
        assert entry["tools"]["fs"]["workspaceOnly"] is True
        assert entry["tools"]["exec"]["mode"] == "ask"
        assert entry["tools"]["elevated"]["enabled"] is False


def test_read_only_roles_cannot_mutate_or_exec() -> None:
    entries = build_openclaw_patch(Path("C:/OpenClawLocal"))["agents"]["entries"]
    for agent_id in (
        "chef-operations",
        "expert-recherche",
        "architecte-solutions",
        "auditeur-qualite",
    ):
        denied = set(entries[agent_id]["tools"]["deny"])
        assert {"write", "edit", "apply_patch", "exec", "process"} <= denied


def test_provider_uses_native_ollama_api_and_16k_prequalification_cap() -> None:
    patch = build_openclaw_patch(Path("C:/OpenClawLocal"))
    provider = patch["models"]["providers"]["ollama"]
    assert provider["api"] == "ollama"
    assert provider["baseUrl"] == "http://127.0.0.1:11434"
    assert "/v1" not in provider["baseUrl"]
    assert len(provider["models"]) == 2
    assert all(model["contextTokens"] == 16384 for model in provider["models"])
