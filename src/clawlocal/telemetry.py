from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract

_NUMERIC_FIELDS = {
    "ttft_ms",
    "duration_ms",
    "prompt_tokens",
    "generated_tokens",
    "tokens_per_second",
    "vram_mb",
    "ram_mb",
    "tool_calls",
    "retries",
    "cloud_cost_eur",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def default_telemetry_path(platform_root: Path) -> Path:
    policy = load_contract("telemetry_policy.yaml")
    return platform_root / str(policy["storage"]["relative_path"])


def _validate_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    payload.setdefault("timestamp", _now())
    if not str(payload.get("event_type", "")).strip():
        raise ValueError("telemetry event_type requis")

    for field in _NUMERIC_FIELDS:
        if field not in payload or payload[field] is None:
            continue
        value = float(payload[field])
        if value < 0:
            raise ValueError(f"telemetry {field} ne peut pas être négatif")

    if payload.get("cloud_cost_eur") is not None and payload.get("cloud_escalation") is not True:
        raise ValueError("cloud_cost_eur exige cloud_escalation=true")

    forbidden = {"prompt", "response", "prompt_content", "response_content", "secret"}
    if forbidden & set(payload):
        raise ValueError("contenu sensible interdit dans la télémétrie")
    return payload


def append_telemetry_event(platform_root: Path, event: dict[str, Any]) -> Path:
    payload = _validate_event(event)
    path = default_telemetry_path(platform_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def read_telemetry_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if not value:
                continue
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                raise ValueError("ligne télémétrie invalide")
            events.append(parsed)
    return events


def summarize_telemetry(
    events: list[dict[str, Any]],
    *,
    project_id: str | None = None,
) -> dict[str, Any]:
    selected = [
        event
        for event in events
        if project_id is None or event.get("project_id") == project_id
    ]
    by_agent: dict[str, int] = defaultdict(int)
    by_model: dict[str, int] = defaultdict(int)
    by_backend: dict[str, int] = defaultdict(int)
    cloud_cost = 0.0
    total_duration = 0.0
    total_generated = 0.0
    total_tool_calls = 0.0
    local_to_deep = 0
    cloud_escalations = 0

    for event in selected:
        if event.get("agent"):
            by_agent[str(event["agent"])] += 1
        if event.get("model"):
            by_model[str(event["model"])] += 1
        if event.get("backend"):
            by_backend[str(event["backend"])] += 1
        cloud_cost += float(event.get("cloud_cost_eur") or 0)
        total_duration += float(event.get("duration_ms") or 0)
        total_generated += float(event.get("generated_tokens") or 0)
        total_tool_calls += float(event.get("tool_calls") or 0)
        if event.get("local_to_deep_transition") is True:
            local_to_deep += 1
        if event.get("cloud_escalation") is True:
            cloud_escalations += 1

    return {
        "event_count": len(selected),
        "project_id": project_id,
        "cloud_cost_eur": round(cloud_cost, 6),
        "duration_ms": round(total_duration, 3),
        "generated_tokens": int(total_generated),
        "tool_calls": int(total_tool_calls),
        "local_to_deep_transitions": local_to_deep,
        "cloud_escalations": cloud_escalations,
        "by_agent": dict(sorted(by_agent.items())),
        "by_model": dict(sorted(by_model.items())),
        "by_backend": dict(sorted(by_backend.items())),
    }


def export_project_summary(platform_root: Path, project: Path) -> Path:
    events = read_telemetry_events(default_telemetry_path(platform_root))
    summary = summarize_telemetry(events, project_id=project.name)
    target = project / "evidence" / "telemetry_summary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target
