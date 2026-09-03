from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from clawlocal.config import load_contract


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_sha(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON invalide: {path}")
    return payload


def _policy() -> dict[str, Any]:
    return load_contract("model_identity_policy.yaml")


def _paths(platform_root: Path) -> tuple[Path, Path]:
    policy = _policy()
    state_root = platform_root / str(policy["state_root"])
    return (
        state_root / str(policy["candidate_filename"]),
        state_root / str(policy["qualified_filename"]),
    )


def _ollama_endpoint() -> str:
    backends = load_contract("runtime_backends.yaml")
    return str(backends["backends"]["ollama-vulkan"]["endpoint"]).rstrip("/")


def current_model_identity(*, timeout_seconds: int = 10) -> dict[str, Any]:
    catalog = load_contract("model_catalog.yaml")
    endpoint = _ollama_endpoint()
    try:
        with urlopen(f"{endpoint}/api/tags", timeout=timeout_seconds) as response:  # noqa: S310
            tags = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"impossible de lire l'identité des modèles Ollama: {exc}") from exc
    models = tags.get("models", []) if isinstance(tags, dict) else []
    if not isinstance(models, list):
        raise ValueError("réponse Ollama /api/tags invalide")

    by_name: dict[str, dict[str, Any]] = {}
    for item in models:
        if not isinstance(item, dict):
            continue
        for key in ("name", "model"):
            name = str(item.get(key, "")).strip()
            if name:
                by_name[name] = item

    identities: dict[str, dict[str, Any]] = {}
    for alias, model in catalog.get("models", {}).items():
        if not isinstance(model, dict) or model.get("provider") != "ollama" or not model.get("required"):
            continue
        runtime_id = str(model["runtime_id"])
        observed = by_name.get(runtime_id)
        if observed is None:
            raise ValueError(f"modèle Ollama requis absent: {runtime_id}")
        digest = str(observed.get("digest", "")).strip()
        if not digest:
            raise ValueError(f"digest Ollama absent pour {runtime_id}")
        details = observed.get("details", {})
        if not isinstance(details, dict):
            details = {}
        identities[str(alias)] = {
            "runtime_id": runtime_id,
            "digest": digest,
            "format": str(details.get("format", "")),
            "family": str(details.get("family", "")),
            "parameter_size": str(details.get("parameter_size", "")),
            "quantization_level": str(details.get("quantization_level", "")),
        }
    if len(identities) != int(catalog.get("policy", {}).get("local_model_count", 3)):
        raise ValueError("identité incomplète: la flotte required n'est pas entièrement résolue")
    return {
        "schema_version": "1.0.0",
        "captured_at": _now(),
        "provider": "ollama",
        "endpoint": endpoint,
        "models": identities,
        "fingerprint_sha256": _canonical_sha(identities),
    }


def capture_candidate(platform_root: Path) -> Path:
    candidate_path, qualified_path = _paths(platform_root)
    current = current_model_identity()
    _write_json(candidate_path, {**current, "status": "CANDIDATE"})
    if qualified_path.is_file():
        qualified = _read_json(qualified_path)
        previous = str(qualified.get("fingerprint_sha256", ""))
        if previous and previous != current["fingerprint_sha256"]:
            qualified["status"] = "INVALIDATED"
            qualified["invalidated_at"] = _now()
            qualified["invalidation_reason"] = "runtime_model_identity_changed"
            qualified["current_fingerprint_sha256"] = current["fingerprint_sha256"]
            _write_json(qualified_path, qualified)
    return candidate_path


def promote_candidate(platform_root: Path) -> Path:
    candidate_path, qualified_path = _paths(platform_root)
    if not candidate_path.is_file():
        raise FileNotFoundError(candidate_path)
    candidate = _read_json(candidate_path)
    current = current_model_identity()
    if candidate.get("fingerprint_sha256") != current.get("fingerprint_sha256"):
        raise PermissionError("identité modèle modifiée pendant la qualification; promotion refusée")
    qualified = {
        **current,
        "status": "QUALIFIED",
        "qualified_at": _now(),
        "qualification_basis": "successful_full_local_qualification",
    }
    _write_json(qualified_path, qualified)
    return qualified_path


def check_qualified(platform_root: Path, *, allow_unqualified: bool = False) -> str:
    _, qualified_path = _paths(platform_root)
    if not qualified_path.is_file():
        if allow_unqualified:
            return "UNQUALIFIED"
        raise FileNotFoundError(qualified_path)
    qualified = _read_json(qualified_path)
    current = current_model_identity()
    if qualified.get("fingerprint_sha256") != current.get("fingerprint_sha256"):
        qualified["status"] = "INVALIDATED"
        qualified["invalidated_at"] = _now()
        qualified["invalidation_reason"] = "runtime_model_identity_changed"
        qualified["current_fingerprint_sha256"] = current["fingerprint_sha256"]
        _write_json(qualified_path, qualified)
        return "INVALIDATED"
    if qualified.get("status") != "QUALIFIED":
        return str(qualified.get("status", "INVALIDATED"))
    return "QUALIFIED"
