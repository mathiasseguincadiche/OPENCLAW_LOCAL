from pathlib import Path

import pytest

from clawlocal.project_intake import create_project
from clawlocal.telemetry import append_telemetry, read_telemetry, summarize_telemetry


def test_telemetry_records_observed_metrics_only(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "telemetry-demo", "Telemetry Demo")
    append_telemetry(
        project,
        {
            "project_id": "telemetry-demo",
            "agent": "ingenieur-devops",
            "model": "devstral-devops",
            "backend": "ollama-vulkan",
            "route_kind": "local_specialist",
            "duration_ms": 1200,
            "ttft_ms": 200,
            "generated_tokens": 120,
            "tokens_per_second": 12.5,
            "tool_calls": 2,
            "success": True,
        },
    )
    rows = read_telemetry(project)
    assert len(rows) == 1
    assert rows[0]["generated_tokens"] == 120
    summary = summarize_telemetry(project)
    assert summary["runs"] == 1
    assert summary["generated_tokens_total"] == 120


def test_telemetry_rejects_private_content_and_negative_metrics(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "telemetry-safe", "Telemetry Safe")
    base = {
        "project_id": "telemetry-safe",
        "agent": "chef-operations",
        "model": "qwen-max",
        "backend": "ollama-vulkan",
        "route_kind": "local_max",
        "duration_ms": 10,
    }
    with pytest.raises(ValueError):
        append_telemetry(project, {**base, "prompt": "secret"})
    with pytest.raises(ValueError):
        append_telemetry(project, {**base, "duration_ms": -1})
