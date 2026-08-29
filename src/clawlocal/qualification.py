from __future__ import annotations

from math import ceil
from statistics import median
from typing import Any


def _percentile(
    values: list[float],
    percentile: float,
) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _ratio(passed: int, total: int) -> float:
    return passed / total if total else 0.0


def _observed_model_aliases(payload: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for model in payload.get("models", []):
        if isinstance(model, dict) and model.get("alias"):
            aliases.append(str(model["alias"]))
    for case in payload.get("cases", []):
        if isinstance(case, dict) and case.get("model_alias"):
            aliases.append(str(case["model_alias"]))
    return list(dict.fromkeys(aliases))


def _evaluate_model(
    alias: str,
    cases: list[dict[str, Any]],
    required_contexts: set[int],
    thresholds: dict[str, Any],
    *,
    required: bool,
) -> dict[str, Any]:
    selected = [
        case
        for case in cases
        if case.get("model_alias") == alias
        and int(case.get("context", 0)) in required_contexts
    ]
    errors = [case for case in selected if case.get("status") != "ok"]
    checked = [case for case in selected if case.get("check_required", True)]
    passed = [case for case in checked if case.get("check_passed") is True]
    tps = [
        float(case["tokens_per_second"])
        for case in selected
        if case.get("tokens_per_second")
    ]
    ttft = [
        float(case["ttft_ms"])
        for case in selected
        if case.get("ttft_ms") is not None
    ]
    observed_contexts = {
        int(case["context"])
        for case in selected
        if case.get("context")
    }

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
    minimum_tps = float(thresholds["min_median_tokens_per_second"])
    if median_tps is None or median_tps < minimum_tps:
        failures.append(f"median_tokens_per_second={median_tps}")
    maximum_ttft = float(thresholds["max_p95_ttft_ms"])
    if p95_ttft_ms is None or p95_ttft_ms > maximum_ttft:
        failures.append(f"p95_ttft_ms={p95_ttft_ms}")

    per_context = thresholds.get("per_context_min_check_pass_rate", {})
    for context_text, minimum in per_context.items():
        context = int(context_text)
        if context not in required_contexts:
            continue
        context_cases = [
            case for case in checked if int(case.get("context", 0)) == context
        ]
        context_passed = [
            case for case in context_cases if case.get("check_passed") is True
        ]
        rate = _ratio(len(context_passed), len(context_cases))
        if not context_cases or rate < float(minimum):
            failures.append(f"context_{context}_check_pass_rate={rate:.3f}")

    return {
        "required": required,
        "cases": len(selected),
        "error_rate": round(error_rate, 4),
        "check_pass_rate": round(check_pass_rate, 4),
        "median_tokens_per_second": (
            round(median_tps, 3) if median_tps is not None else None
        ),
        "p95_ttft_ms": (
            round(p95_ttft_ms, 3) if p95_ttft_ms is not None else None
        ),
        "observed_contexts": sorted(observed_contexts),
        "automated_gate": "pass" if not failures else "fail",
        "failures": failures,
    }


def evaluate_benchmark(
    payload: dict[str, Any],
    policy: dict[str, Any],
    *,
    required_contexts_override: set[int] | None = None,
    pass_verdict: str | None = None,
) -> dict[str, Any]:
    expected_suite = policy.get("suite")
    observed_suite = payload.get("suite")
    if expected_suite is not None and observed_suite != expected_suite:
        raise ValueError(
            f"suite benchmark inattendue: {observed_suite!r}, "
            f"attendu {expected_suite!r}"
        )

    gates = policy["automated_gates"]
    thresholds = gates["thresholds"]
    required_models = [str(alias) for alias in gates["required_models"]]
    required_set = set(required_models)
    if required_contexts_override is None:
        required_contexts = {int(value) for value in policy["required_contexts"]}
        evaluation_mode = "qualification"
    else:
        required_contexts = {int(value) for value in required_contexts_override}
        if not required_contexts:
            raise ValueError("required_contexts_override ne peut pas être vide")
        evaluation_mode = "diagnostic"
    cases = [case for case in payload.get("cases", []) if isinstance(case, dict)]

    observed_aliases = _observed_model_aliases(payload)
    evaluated_aliases = list(dict.fromkeys(required_models + observed_aliases))
    model_reports = {
        alias: _evaluate_model(
            alias,
            cases,
            required_contexts,
            thresholds,
            required=alias in required_set,
        )
        for alias in evaluated_aliases
    }

    automated_pass = all(
        model_reports.get(alias, {}).get("automated_gate") == "pass"
        for alias in required_models
    )
    optional_candidates = {
        alias: report
        for alias, report in model_reports.items()
        if alias not in required_set
    }
    optional_pass = sorted(
        alias
        for alias, report in optional_candidates.items()
        if report["automated_gate"] == "pass"
    )
    optional_fail = sorted(
        alias
        for alias, report in optional_candidates.items()
        if report["automated_gate"] != "pass"
    )

    ready_verdict = pass_verdict or policy["promotion"]["ready_verdict"]
    return {
        "schema_version": "1.1.0",
        "suite": observed_suite,
        "evaluation_mode": evaluation_mode,
        "evaluated_contexts": sorted(required_contexts),
        "automated_gate": "pass" if automated_pass else "fail",
        "verdict": ready_verdict if automated_pass else "NOT_READY",
        "automatic_promotion": False,
        "manual_requirements": list(policy["promotion"]["requires"]),
        "required_models": required_models,
        "optional_candidates": {
            "passed": optional_pass,
            "failed": optional_fail,
            "promotion_is_independent": True,
        },
        "models": model_reports,
    }
