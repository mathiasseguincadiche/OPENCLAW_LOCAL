from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_qualification_docs_match_active_hard40_contract() -> None:
    policy = yaml.safe_load(_read("config/v1/qualification_policy.yaml"))
    budget = policy["runtime_budget"]

    launcher = _read("scripts/windows/05_benchmark.ps1")
    runner_match = re.search(r"benchmark_qualification_40m_v\d+\.py", launcher)
    assert runner_match is not None
    runner_name = runner_match.group(0)
    runner = _read(f"scripts/{runner_name}")

    qwen_match = re.search(
        r"QWEN_NATIVE_MAX_OUTPUT_TOKENS\s*=\s*(\d+)",
        runner,
    )
    assert qwen_match is not None
    qwen_native_max = int(qwen_match.group(1))

    expected_markers = (
        runner_name,
        f"{qwen_native_max} tokens",
        f"{int(budget['qualification_max_wall_seconds'])} s",
        f"{int(budget['evaluation_reserve_seconds'])} s",
        f"{int(budget['benchmark_default_max_wall_seconds'])} s",
        f"{int(budget['max_case_wall_seconds'])} s",
    )

    for relative in ("docs/QUALIFICATION.md", "docs/BENCHMARK.md"):
        text = _read(relative)
        for marker in expected_markers:
            assert marker in text, f"{relative}: contrat absent ou obsolète: {marker}"
        assert "640 tokens" not in text
        assert "150 s maximum" not in text


def test_qualification_docs_distinguish_identity_lock_from_v1_promotion() -> None:
    qualification = _read("docs/QUALIFICATION.md")
    benchmark = _read("docs/BENCHMARK.md")

    assert "qualified_model_identity.json" in qualification
    assert "INVALIDATED" in qualification
    assert "uniquement après un gate complet PASS" in qualification
    assert "aucune promotion automatique de backend" in qualification

    assert "ne promeut ce fingerprint" in benchmark
    assert "ne modifie ni le catalogue" in benchmark
    assert "Le mode `-Quick` ne promeut jamais" in benchmark
