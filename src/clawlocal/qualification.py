from __future__ import annotations

from math import ceil
from statistics import median
from typing import Any


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _ratio(passed: int, total: int) -> float:
    return passed / total if total else 0.0


def evaluate_benchmark(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    gates = policy["automated_gates"]
    thresholds = gates["thresholds"]
    required_models = list(gates["required_models"])
    required_contexts = {int(value) for value in policy["required_contexts"]}
    cases = list(payload.get("cases", []))
    model_reports: dict[str, Any] = {}

    for alias in required_models:
        selected = [case for case in cases if case.get("model_alias") == alias]
        errors = [case for case in selected if case.get("status") != "ok"]
        checked = [case for case in selected if case.get("check_required", True)]
        passed = [case for case in checked if case.get("check_passed") is True]
        tps = [float(case["tokens_per_second"]) for case in selected if case.get("tokens_per_second")]
        ttft = [float(case["ttft_ms"]) for case in selected if case.get("ttft_ms") is not None]
        observed_contexts = {int(case["context"]) for case in selected if case.get("context")}

        error_rate = _ratio(len(errors), len(selected))
        check_pass_rate = _ratio(len(passed), len(checked))
        median_tps = median(tps) if tps else None
        p95_ttft_ms = _percentile(ttft, 0.95)
        failures: list[str] = []

        missing_contexts = sorted(required_contexts - observed_contexts)
        if missing_contexts:
            failures.append(f"contextes requis absents: {missing_contexts}")
        if error_rate > float(thresholds["max_error_rate"]):
            failures.append(f"error_rate={error_rate:.3f}")
        if check_pass_rate < float(thresholds["min_check_pass_rate"]):
            failures.append(f"check_pass_rate={check_pass_rate:.3f}")
        if median_tps is None or median_tps < float(thresholds["min_median_tokens_per_second"]):
            failures.append(f"median_tokens_per_second={median_tps}")
        if p95_ttft_ms is None or p95_ttft_ms > float(thresholds["max_p95_ttft_ms"]):
            failures.append(f"p95_ttft_ms={p95_ttft_ms}")

        for context_text, minimum in thresholds.get("per_context_min_check_pass_rate", {}).items():
            context = int(context_text)
            context_cases = [case for case in checked if int(case.get("context", 0)) == context]
            context_passed = [case for case in context_cases if case.get("check_passed") is True]
            rate = _ratio(len(context_passed), len(context_cases))
            if not context_cases or rate < float(minimum):
                failures.append(f"context_{context}_check_pass_rate={rate:.3f}")

        model_reports[alias] = {
            "cases": len(selected),
            "error_rate": round(error_rate, 4),
            "check_pass_rate": round(check_pass_rate, 4),
            "median_tokens_per_second": round(median_tps, 3) if median_tps is not None else None,
            "p95_ttft_ms": round(p95_ttft_ms, 3) if p95_ttft_ms is not None else None,
            "observed_contexts": sorted(observed_contexts),
            "automated_gate": "pass" if not failures else "fail",
            "failures": failures,
        }

    automated_pass = all(
        model_reports.get(alias, {}).get("automated_gate") == "pass" for alias in required_models
    )
    ready_verdict = policy["promotion"]["ready_verdict"]
    return {
        "schema_version": "1.0.0",
        "suite": payload.get("suite"),
        "automated_gate": "pass" if automated_pass else "fail",
        "verdict": ready_verdict if automated_pass else "NOT_READY",
        "automatic_promotion": False,
        "manual_requirements": list(policy["promotion"]["requires"]),
        "models": model_reports,
    }
