from clawlocal.qualification import evaluate_benchmark

REQUIRED_MODELS = ("qwen-max", "gemma-deep", "devstral-devops")


def policy() -> dict:
    return {
        "required_contexts": [8192, 16384],
        "automated_gates": {
            "required_models": list(REQUIRED_MODELS),
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
    for alias in REQUIRED_MODELS:
        cases.extend(_model_cases(alias))
    return {"suite": "devops-v1", "cases": cases}


def test_passing_performance_fleet_requires_manual_qualification() -> None:
    report = evaluate_benchmark(passing_payload(), policy())
    assert report["automated_gate"] == "pass"
    assert report["verdict"] == "READY_FOR_MANUAL_QUALIFICATION"
    assert report["evaluation_mode"] == "qualification"
    assert report["evaluated_contexts"] == [8192, 16384]
    assert report["automatic_promotion"] is False
    assert set(report["required_models"]) == set(REQUIRED_MODELS)
    assert all(report["models"][alias]["required"] for alias in REQUIRED_MODELS)
    assert report["optional_candidates"]["passed"] == []
    assert report["optional_candidates"]["failed"] == []


def test_missing_required_context_fails_all_three_models() -> None:
    payload = passing_payload()
    payload["cases"] = [case for case in payload["cases"] if case["context"] == 8192]
    report = evaluate_benchmark(payload, policy())
    assert report["automated_gate"] == "fail"
    assert report["verdict"] == "NOT_READY"
    assert all(
        report["models"][alias]["automated_gate"] == "fail"
        for alias in REQUIRED_MODELS
    )


def test_quick_8k_diagnostic_does_not_require_16k_or_claim_qualification() -> None:
    payload = passing_payload()
    payload["cases"] = [case for case in payload["cases"] if case["context"] == 8192]
    report = evaluate_benchmark(
        payload,
        policy(),
        required_contexts_override={8192},
        pass_verdict="QUICK_DIAGNOSTIC_PASS",
    )
    assert report["automated_gate"] == "pass"
    assert report["verdict"] == "QUICK_DIAGNOSTIC_PASS"
    assert report["evaluation_mode"] == "diagnostic"
    assert report["evaluated_contexts"] == [8192]
    assert report["automatic_promotion"] is False
    assert all(
        report["models"][alias]["observed_contexts"] == [8192]
        for alias in REQUIRED_MODELS
    )


def test_failure_of_any_supported_model_fails_whole_fleet_gate() -> None:
    payload = passing_payload()
    payload["cases"] = [
        case
        for case in payload["cases"]
        if case["model_alias"] != "devstral-devops"
    ]
    payload["cases"].extend(_model_cases("devstral-devops", passing=False))
    report = evaluate_benchmark(payload, policy())
    assert report["automated_gate"] == "fail"
    assert report["models"]["devstral-devops"]["automated_gate"] == "fail"
    assert report["models"]["qwen-max"]["automated_gate"] == "pass"
    assert report["models"]["gemma-deep"]["automated_gate"] == "pass"


def test_api_error_on_qwen_max_fails_gate() -> None:
    payload = passing_payload()
    payload["cases"][0]["status"] = "error"
    payload["cases"][0]["check_passed"] = False
    report = evaluate_benchmark(payload, policy())
    assert report["models"]["qwen-max"]["automated_gate"] == "fail"
    assert report["automated_gate"] == "fail"
