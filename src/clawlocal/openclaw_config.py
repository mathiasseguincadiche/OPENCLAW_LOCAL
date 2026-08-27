from __future__ import annotations

from pathlib import Path
from typing import Any

from clawlocal.config import load_contract


def _local_ref(alias: str, catalog: dict[str, Any]) -> str:
    model = catalog["models"][alias]
    provider = model["provider"]
    if provider == "ollama":
        return f"ollama/{model['runtime_id']}"
    if provider == "llama_cpp":
        return f"llamacpp/{model['runtime_id']}"
    raise ValueError(
        f"Le modèle {alias} utilise {provider}; "
        "import/backend et qualification explicites requis"
    )


def _agent_tools(
    agent_id: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    entry = policy["agents"][agent_id]
    tools: dict[str, Any] = {
        "profile": entry["profile"],
        "fs": {
            "workspaceOnly": bool(
                policy["security_defaults"]["fs_workspace_only"]
            )
        },
        "exec": {"mode": policy["security_defaults"]["exec_mode"]},
        "elevated": {
            "enabled": bool(
                policy["security_defaults"]["elevated_enabled"]
            )
        },
    }
    if entry.get("also_allow"):
        tools["alsoAllow"] = list(entry["also_allow"])
    if entry.get("deny"):
        tools["deny"] = list(entry["deny"])
    return tools


def _ollama_models(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for alias, model in catalog["models"].items():
        if model["provider"] != "ollama":
            continue
        models.append(
            {
                "id": model["runtime_id"],
                "name": model["runtime_id"],
                "input": list(model.get("input", ["text"])),
                "contextTokens": 16384,
                "params": {
                    "num_ctx": 16384,
                    "keep_alive": "15m",
                },
                "metadata": {
                    "clawlocalAlias": alias,
                    "status": model.get("status"),
                },
            }
        )
    return models


def build_openclaw_patch(platform_root: Path) -> dict[str, Any]:
    """Build the deterministic OpenClaw patch for the local-first fleet."""
    catalog = load_contract("model_catalog.yaml")
    routing = load_contract("model_routing.yaml")
    tool_policy = load_contract("tool_policy.yaml")
    web_policy = load_contract("web_policy.yaml")

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
            "model": {
                "primary": primary,
                "fallbacks": fallbacks,
            },
            "experimental": {"localModelLean": True},
            "tools": _agent_tools(agent_id, tool_policy),
        }

    qwen = catalog["models"]["qwen-general"]["runtime_id"]
    gemma = catalog["models"]["gemma-review"]["runtime_id"]
    web = web_policy["nominal_path"]
    return {
        "gateway": {
            "mode": "local",
            "bind": "loopback",
        },
        "models": {
            "providers": {
                "ollama": {
                    "baseUrl": "http://127.0.0.1:11434",
                    "apiKey": "ollama-local",
                    "api": "ollama",
                    "timeoutSeconds": 300,
                    "models": _ollama_models(catalog),
                }
            }
        },
        "agents": {
            "ownership": "explicit",
            "defaults": {
                "skipBootstrap": True,
                "model": {
                    "primary": f"ollama/{qwen}",
                    "fallbacks": [f"ollama/{gemma}"],
                },
            },
            "entries": entries,
        },
        "tools": {
            "profile": tool_policy["security_defaults"]["profile"],
            "fs": {
                "workspaceOnly": bool(
                    tool_policy["security_defaults"]["fs_workspace_only"]
                )
            },
            "exec": {
                "mode": tool_policy["security_defaults"]["exec_mode"],
                "applyPatch": {"workspaceOnly": True},
            },
            "elevated": {
                "enabled": bool(
                    tool_policy["security_defaults"]["elevated_enabled"]
                )
            },
            "web": {
                "search": {
                    "enabled": bool(web["web_search_enabled"]),
                    "provider": web["search_provider"],
                    "maxResults": int(web["max_results"]),
                    "timeoutSeconds": int(web["search_timeout_seconds"]),
                    "cacheTtlMinutes": int(web["cache_ttl_minutes"]),
                },
                "fetch": {
                    "enabled": bool(web["web_fetch_enabled"]),
                    "maxChars": 20000,
                    "maxCharsCap": 20000,
                    "timeoutSeconds": 30,
                },
            },
        },
    }
