from __future__ import annotations

from pathlib import Path
from typing import Any

from clawlocal.config import load_contract

SUPPORTED_BACKENDS = ("ollama-vulkan", "llama-cpp-sycl")
INTEL_SYCL_PROVIDER_ID = "intel-sycl"


def _backend_ref(alias: str, catalog: dict[str, Any], backend_id: str) -> str:
    model = catalog["models"][alias]
    if backend_id == "ollama-vulkan":
        return f"ollama/{model['runtime_id']}"
    if backend_id == "llama-cpp-sycl":
        return f"{INTEL_SYCL_PROVIDER_ID}/{model['runtime_id']}"
    raise ValueError(f"Backend local non supporté pour OpenClaw: {backend_id}")


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
    for model in catalog["models"].values():
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
            }
        )
    return models


def _intel_sycl_models(
    catalog: dict[str, Any],
    context_tokens: int,
) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for model in catalog["models"].values():
        if not model.get("required"):
            continue
        runtime_id = str(model["runtime_id"])
        models.append(
            {
                "id": runtime_id,
                "name": runtime_id,
                # Le premier parcours SYCL est volontairement texte uniquement.
                # Image/PDF restent sur Ollama jusqu'à qualification mmproj dédiée.
                "input": ["text"],
                "contextWindow": context_tokens,
                "contextTokens": context_tokens,
                "maxTokens": 2048,
                "cost": {
                    "input": 0,
                    "output": 0,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
                "compat": {"toolSchemaProfile": "llamacpp"},
            }
        )
    return models


def _ollama_provider(catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseUrl": "http://127.0.0.1:11434",
        "apiKey": "ollama-local",
        "api": "ollama",
        "timeoutSeconds": 300,
        "models": _ollama_models(catalog),
    }


def _model_providers(
    catalog: dict[str, Any],
    backends: dict[str, Any],
    backend_id: str,
) -> dict[str, Any]:
    providers: dict[str, Any] = {"ollama": _ollama_provider(catalog)}
    if backend_id == "ollama-vulkan":
        return providers

    backend = backends["backends"][backend_id]
    context_tokens = int(backend["router"]["context_tokens"])
    providers[INTEL_SYCL_PROVIDER_ID] = {
        "baseUrl": str(backend["endpoint"]),
        "apiKey": "intel-sycl-local",
        "api": "openai-completions",
        "timeoutSeconds": 300,
        "models": _intel_sycl_models(catalog, context_tokens),
    }
    return providers


def build_openclaw_patch(
    platform_root: Path,
    backend_id: str = "ollama-vulkan",
) -> dict[str, Any]:
    """Build the deterministic OpenClaw patch for one explicit local backend."""
    if backend_id not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"Backend OpenClaw invalide: {backend_id}; "
            f"attendus: {', '.join(SUPPORTED_BACKENDS)}"
        )

    catalog = load_contract("model_catalog.yaml")
    routing = load_contract("model_routing.yaml")
    tool_policy = load_contract("tool_policy.yaml")
    web_policy = load_contract("web_policy.yaml")
    ingestion_policy = load_contract("document_ingestion_policy.yaml")
    backends = load_contract("runtime_backends.yaml")

    configured_backends = backends.get("backends", {})
    if backend_id not in configured_backends:
        raise ValueError(f"Backend absent de runtime_backends.yaml: {backend_id}")

    workspaces_root = platform_root / "workspaces"
    agent_list: list[dict[str, Any]] = []
    for agent_id, route in routing["agents"].items():
        primary = _backend_ref(route["local_primary"], catalog, backend_id)
        fallbacks: list[str] = []
        fallback_alias = route.get("local_fallback")
        if fallback_alias:
            fallbacks.append(_backend_ref(fallback_alias, catalog, backend_id))
        agent_list.append(
            {
                "id": agent_id,
                "default": agent_id == "chef-operations",
                "name": agent_id,
                "workspace": str(workspaces_root / agent_id),
                "model": {
                    "primary": primary,
                    "fallbacks": fallbacks,
                },
                "experimental": {"localModelLean": True},
                "tools": _agent_tools(agent_id, tool_policy),
            }
        )

    qwen = str(catalog["models"]["qwen-max"]["runtime_id"])
    gemma = str(catalog["models"]["gemma-deep"]["runtime_id"])
    qwen_text_ref = _backend_ref("qwen-max", catalog, backend_id)
    gemma_text_ref = _backend_ref("gemma-deep", catalog, backend_id)
    # Le multimodal reste sciemment sur le backend déjà validé. Les blobs GGUF
    # texte ne suffisent pas à prouver la présence/compatibilité des projecteurs.
    qwen_multimodal_ref = f"ollama/{qwen}"
    gemma_multimodal_ref = f"ollama/{gemma}"

    web = web_policy["nominal_path"]
    pdf_policy = ingestion_policy.get("formats", {}).get("pdf", {})
    return {
        "gateway": {
            "mode": "local",
            "bind": "loopback",
        },
        "models": {
            "providers": _model_providers(catalog, backends, backend_id),
        },
        "agents": {
            "defaults": {
                "skipBootstrap": True,
                "model": {
                    "primary": qwen_text_ref,
                    "fallbacks": [gemma_text_ref],
                },
                "imageModel": {
                    "primary": qwen_multimodal_ref,
                    "fallbacks": [gemma_multimodal_ref],
                },
                "pdfModel": {
                    "primary": qwen_multimodal_ref,
                    "fallbacks": [gemma_multimodal_ref],
                },
                "pdfMaxBytesMb": int(pdf_policy.get("max_bytes_mb", 50)),
                "pdfMaxPages": int(pdf_policy.get("max_pages_per_tool_call", 20)),
            },
            "list": agent_list,
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
