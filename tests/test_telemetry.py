from pathlib import Path

import pytest

from clawlocal.telemetry import (
    append_telemetry_event,
    default_telemetry_path,
    read_telemetry_events,
    summarize_telemetry,
)


def test_telemetry_records_operational_metrics_without_content(tmp_path: Path) -> None:
    append_telemetry_event(
        tmp_path,
        {
            "event_type": "agent_call",
            "project_id": "p4-devops",
            "agent": "ingenieur-devops",
            "model": "qwen3.5:9b",
            "backend": "ollama-vulkan",
            "duration_ms": 1500,
            "generated_tokens": 300,
            "tool_calls": 2,
            "local_to_deep_transition": False,
            "cloud_escalation": False,
        },
    )
    events = read_telemetry_events(default_telemetry_path(tmp_path))
    summary = summarize_telemetry(events, project_id="p4-devops")
    assert summary["event_count"] == 1
    assert summary["generated_tokens"] == 300
    assert summary["by_agent"] == {"ingenieur-devops": 1}


def test_telemetry_rejects_sensitive_content_and_invalid_cloud_cost(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="contenu sensible"):
        append_telemetry_event(
            tmp_path,
            {"event_type": "agent_call", "prompt_content": "secret"},
        )
    with pytest.raises(ValueError, match="cloud_cost_eur"):
        append_telemetry_event(
            tmp_path,
            {
                "event_type": "agent_call",
                "cloud_escalation": False,
                "cloud_cost_eur": 0.10,
            },
        )
