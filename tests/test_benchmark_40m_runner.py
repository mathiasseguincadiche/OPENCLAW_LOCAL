from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import benchmark_local as core  # noqa: E402
import benchmark_qualification_40m as hard40  # noqa: E402


def load_inputs() -> tuple[dict, dict, dict, list[dict]]:
    catalog = core.load_yaml(ROOT / "config" / "v1" / "model_catalog.yaml")
    policy = core.load_yaml(ROOT / "config" / "v1" / "qualification_policy.yaml")
    suite = core.load_yaml(ROOT / "benchmarks" / "suites" / "devops_v2.yaml")
    models = [
        {"alias": alias, **catalog["models"][alias]}
        for alias in policy["automated_gates"]["required_models"]
    ]
    return catalog, policy, suite, models


def test_hard_40m_policy_is_strictly_bounded() -> None:
    _, policy, _, _ = load_inputs()
    budget = hard40._runtime_budget(policy)
    assert budget["qualification"] == 2400
    assert budget["benchmark"] == 2100
    assert budget["case"] == 210


def test_matrix_has_30_cases_with_24_8k_and_6_16k() -> None:
    _, policy, suite, models = load_inputs()
    plan = hard40._matrix_plan(policy, suite, models)
    assert len(plan) == 30
    contexts = Counter(context for _, context, _ in plan)
    assert contexts == Counter({8192: 24, 16384: 6})

    per_model = Counter(str(model["alias"]) for model, _, _ in plan)
    assert per_model == Counter(
        {"qwen-max": 10, "gemma-deep": 10, "devstral-devops": 10}
    )


def test_baseline_collectively_covers_all_twelve_scenarios() -> None:
    _, policy, suite, models = load_inputs()
    plan = hard40._matrix_plan(policy, suite, models)
    observed = {
        str(scenario["id"])
        for _, context, scenario in plan
        if context == 8192
    }
    expected = {str(scenario["id"]) for scenario in suite["scenarios"]}
    assert observed == expected
    assert len(expected) == 12


def test_qwen_native_thinking_is_limited_to_three_probes() -> None:
    _, policy, suite, models = load_inputs()
    plan = hard40._matrix_plan(policy, suite, models)
    native = [
        (context, str(scenario["id"]))
        for model, context, scenario in plan
        if hard40._qwen_native_case(
            str(model["alias"]), context, str(scenario["id"]), policy
        )
    ]
    assert native == [
        (8192, "project-intake-analysis"),
        (8192, "kubernetes-root-cause"),
        (16384, "long-context-discipline"),
    ]


def test_qwen_non_probe_disables_thinking_but_native_probe_is_bounded() -> None:
    _, policy, _, models = load_inputs()
    qwen = next(model for model in models if model["alias"] == "qwen-max")

    limit, think, mode = hard40._generation_policy(
        qwen, 8192, "web-freshness-discipline", 96, policy
    )
    assert (limit, think, mode) == (96, False, "off")

    limit, think, mode = hard40._generation_policy(
        qwen, 8192, "project-intake-analysis", 320, policy
    )
    assert limit == hard40.QWEN_NATIVE_MAX_OUTPUT_TOKENS == 640
    assert think is None
    assert mode == "native"


def test_bounded_generation_rejects_expired_deadline_without_network() -> None:
    with pytest.raises(TimeoutError, match="budget mural"):
        hard40.run_generation_bounded(
            "http://127.0.0.1:9",
            "dummy:model",
            "test",
            8192,
            0.1,
            32,
            think=False,
            deadline=time.perf_counter() - 1,
        )
