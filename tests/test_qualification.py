from __future__ import annotations

from clawlocal.qualification import evaluate_benchmark


def policy() -> dict:
    return {
        "required_contexts": [8192, 16384],
        "automated_gates": {
            "required_models": ["qwen-general", "gemma-review"],
            "thresholds": {
                "max_error_rate": 0.0,
                "min_check_pass_rate": 0.875,
                "min_median_tokens_per_second": 6.0,
                "max_p95_ttft_ms": 12000,
                "per_context_min_check_pass_rate": {"8192": 0.875, "16384": 0.75},
            },
        },
        "promotion": {
            "ready_verdict": "READY_FOR_MANUAL_QUALIFICATION",
            "requires": ["automated_gate_pass", "human_review"],
        },
    }


def _model_cases(alias: str, *, passing: bool = True) -> list[dict]:
    cases = []
    for context in (8192, 16384):
        for index in range(8):
            cases.append(
                {
                    "model_alias": alias,
                    "context": context,
                    "scenario_id": f"{alias}-case-{index}",
                    "status": "ok",
                    "check_required": True,
                    "check_passed": passing,
                    "tokens_per_second": 20.0 if passing else 4.0,
                    "ttft_ms": 500.0,
                }
            )
    return cases


def passing_payload() -> dict:
    cases = []
    for alias in ("qwen-general", "gemma-review"):
        cases.extend(_model_cases(alias))
    return {"suite": "devops-v1", "cases": cases}


def test_passing_benchmark_requires_manual_qualification() -> None:
    report = evaluate_benchmark(passing_payload(), policy())
    assert report["automated_gate"] == "pass"
    assert report["verdict"] == "READY_FOR_MANUAL_QUALIFICATION"
    assert report["automatic_promotion"] is False
    assert all(report["models"][alias]["required"] for alias in report["required_models"])


def test_missing_required_context_fails_gate() -> None:
    payload = passing_payload()
    payload["cases"] = [case for case in payload["cases"] if case["context"] == 8192]
    report = evaluate_benchmark(payload, policy())
    assert report["automated_gate"] == "fail"
    assert report["verdict"] == "NOT_READY"
    assert all(model["automated_gate"] == "fail" for model in report["models"].values())


def test_api_error_fails_gate() -> None:
    payload = passing_payload()
    payload["cases"][0]["status"] = "error"
    payload["cases"][0]["check_passed"] = False
    report = evaluate_benchmark(payload, policy())
    assert report["models"]["qwen-general"]["automated_gate"] == "fail"


def test_optional_candidate_gets_independent_pass_report() -> None:
    payload = passing_payload()
    payload["models"] = [{"alias": "qwen-max"}]
    payload["cases"].extend(_model_cases("qwen-max"))
    report = evaluate_benchmark(payload, policy())
    assert report["automated_gate"] == "pass"
    assert report["models"]["qwen-max"]["required"] is False
    assert report["models"]["qwen-max"]["automated_gate"] == "pass"
    assert report["optional_candidates"]["passed"] == ["qwen-max"]
    assert report["optional_candidates"]["failed"] == []


def test_optional_candidate_failure_does_not_break_required_gate() -> None:
    payload = passing_payload()
    payload["models"] = [{"alias": "devstral-devops"}]
    payload["cases"].extend(_model_cases("devstral-devops", passing=False))
    report = evaluate_benchmark(payload, policy())
    assert report["automated_gate"] == "pass"
    assert report["verdict"] == "READY_FOR_MANUAL_QUALIFICATION"
    assert report["models"]["devstral-devops"]["automated_gate"] == "fail"
    assert report["optional_candidates"]["failed"] == ["devstral-devops"]
