from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract

_REQUIRED = {
    "project_id",
    "agent",
    "model",
    "backend",
    "route_kind",
    "duration_ms",
}
_NUMERIC_NONNEGATIVE = {
    "duration_ms",
    "ttft_ms",
    "tokens_per_second",
    "prompt_tokens",
    "generated_tokens",
    "vram_mb",
    "ram_mb",
    "tool_calls",
    "retries",
    "cloud_cost_eur",
}
_FORBIDDEN_KEYS = {
    "prompt",
    "response",
    "content",
    "document",
    "secret",
    "api_key",
    "token_value",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def telemetry_path(project: Path) -> Path:
    policy = load_contract("telemetry_policy.yaml")
    relative = policy.get("storage", {}).get(
        "relative_path",
        "evidence/telemetry/runs.jsonl",
    )
    return project / str(relative)


def _validate_measurement(payload: dict[str, Any]) -> None:
    missing = sorted(_REQUIRED - set(payload))
    if missing:
        raise ValueError("télémétrie incomplète: " + ", ".join(missing))
    forbidden = sorted(_FORBIDDEN_KEYS & set(payload))
    if forbidden:
        raise ValueError(
            "champs sensibles interdits en télémétrie: " + ", ".join(forbidden)
        )
    for key in _NUMERIC_NONNEGATIVE:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"métrique numérique invalide: {key}")
        if value < 0:
            raise ValueError(f"métrique négative interdite: {key}")
    if payload.get("route_kind") == "cloud_escalation":
        payload["cloud_escalation"] = True


def append_telemetry(project: Path, measurement: dict[str, Any]) -> Path:
    payload = dict(measurement)
    _validate_measurement(payload)
    payload.setdefault("timestamp", _now())
    path = telemetry_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def read_telemetry(project: Path) -> list[dict[str, Any]]:
    path = telemetry_path(project)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("ligne de télémétrie invalide")
            rows.append(payload)
    return rows


def summarize_telemetry(project: Path) -> dict[str, Any]:
    rows = read_telemetry(project)
    durations = [float(row["duration_ms"]) for row in rows if "duration_ms" in row]
    generated = [
        float(row["generated_tokens"])
        for row in rows
        if row.get("generated_tokens") is not None
    ]
    cloud_costs = [
        float(row["cloud_cost_eur"])
        for row in rows
        if row.get("cloud_cost_eur") is not None
    ]
    return {
        "runs": len(rows),
        "duration_ms_total": sum(durations),
        "generated_tokens_total": sum(generated),
        "cloud_cost_eur_total": round(sum(cloud_costs), 6),
        "cloud_escalations": sum(
            1 for row in rows if row.get("cloud_escalation") is True
        ),
        "local_to_deep_transitions": sum(
            1 for row in rows if row.get("local_to_deep_transition") is True
        ),
    }
