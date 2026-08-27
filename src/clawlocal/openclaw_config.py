from __future__ import annotations

from pathlib import Path
from typing import Any

from clawlocal.config import load_contract


def _local_ref(alias: str, catalog: dict[str, Any]) -> str:
    model = catalog["models"][alias]
    if model["provider"] != "ollama":
        raise ValueError(f"Le modèle {alias} n'est pas un modèle Ollama activable automatiquement")
    return f"ollama/{model['runtime_id']}"


def _agent_tools(agent_id: str, policy: dict[str, Any]) -> dict[str, Any]:
    entry = policy["agents"][agent_id]
    tools: dict[str, Any] = {
        "profile": entry["profile"],
        "fs": {"workspaceOnly": bool(policy["security_defaults"]["fs_workspace_only"])},
        "exec": {"mode": policy["security_defaults"]["exec_mode"]},
        "elevated": {
            "enabled": bool(policy["security_defaults"]["elevated_enabled"]),
        },
    }
    if entry.get("deny"):
        tools["deny"] = list(entry["deny"])
    return tools


def build_openclaw_patch(platform_root: Path) -> dict[str, Any]:
    """Build the deterministic OpenClaw patch for the eight-agent local-first fleet."""
    catalog = load_contract("model_catalog.yaml")
    routing = load_contract("model_routing.yaml")
    tool_policy = load_contract("tool_policy.yaml")

    workspaces_root = platform_root / "workspaces"
    entries: dict[str, Any] = {}
    for agent_id, route in routing["agents"].items():
        primary = _local_ref(route["local_primary"], catalog)
        fallbacks: list[str] = []
        fallback_alias = route.get("local_fallback")
        if fallback_alias:
            fallbacks.append(_local_ref(fallback_alias, catalog))

        entries[agent_id] = {
            "name": agent_id,
            "workspace": str(workspaces_root / agent_id),
            "model": {"primary": primary, "fallbacks": fallbacks},
            "experimental": {"localModelLean": True},
            "tools": _agent_tools(agent_id, tool_policy),
        }

    qwen = catalog["models"]["qwen-general"]["runtime_id"]
    gemma = catalog["models"]["gemma-review"]["runtime_id"]

    return {
        "models": {
            "providers": {
                "ollama": {
                    "baseUrl": "http://127.0.0.1:11434",
                    "apiKey": "ollama-local",
                    "api": "ollama",
                    "timeoutSeconds": 300,
                    "models": [
                        {
                            "id": qwen,
                            "name": qwen,
                            "input": ["text"],
                            "contextTokens": 16384,
                            "params": {"num_ctx": 16384, "keep_alive": "15m"},
                        },
                        {
                            "id": gemma,
                            "name": gemma,
                            "input": ["text"],
                            "contextTokens": 16384,
                            "params": {"num_ctx": 16384, "keep_alive": "15m"},
                        },
                    ],
                }
            }
        },
        "agents": {
            "ownership": "explicit",
            "defaults": {
                "skipBootstrap": True,
                "model": {"primary": f"ollama/{qwen}", "fallbacks": [f"ollama/{gemma}"]},
            },
            "entries": entries,
        },
        "tools": {
            "profile": tool_policy["security_defaults"]["profile"],
            "fs": {
                "workspaceOnly": bool(tool_policy["security_defaults"]["fs_workspace_only"])
            },
            "exec": {
                "mode": tool_policy["security_defaults"]["exec_mode"],
                "applyPatch": {"workspaceOnly": True},
            },
            "elevated": {
                "enabled": bool(tool_policy["security_defaults"]["elevated_enabled"])
            },
        },
    }
