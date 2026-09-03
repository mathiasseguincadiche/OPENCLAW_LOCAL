from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "qwen_native_calibration",
    SCRIPTS / "50_calibrate_qwen_native.py",
)
assert SPEC is not None and SPEC.loader is not None
CALIBRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CALIBRATION)


def test_calibration_defaults_leave_qualification_contract_untouched() -> None:
    assert CALIBRATION.DEFAULT_MAX_OUTPUT_TOKENS == 1536
    assert CALIBRATION.DEFAULT_CASE_TIMEOUT_SECONDS == 480.0
    assert CALIBRATION.DEFAULT_THINKING_MODE == "native"
    assert CALIBRATION.THINKING_MODES == ("native", "off")
    assert CALIBRATION.QWEN_ALIAS == "qwen-max"


def test_thinking_modes_map_to_ollama_contract() -> None:
    assert CALIBRATION._thinking_value("native") is None
    assert CALIBRATION._thinking_value("off") is False


def test_native_plan_uses_exact_policy_probes() -> None:
    policy = CALIBRATION.core.load_yaml(
        ROOT / "config" / "v1" / "qualification_policy.yaml"
    )
    suite = CALIBRATION.core.load_yaml(
        CALIBRATION.core.suite_path(str(policy["suite"]))
    )
    plan = CALIBRATION._native_plan(policy, suite)
    observed = [(context, str(scenario["id"])) for context, scenario in plan]
    assert observed == [
        (8192, "project-intake-analysis"),
        (8192, "kubernetes-root-cause"),
        (16384, "long-context-discipline"),
    ]


def test_case_record_hashes_output_without_persisting_raw_text() -> None:
    output = "sensitive synthetic output"
    record = CALIBRATION._case_record(
        repeat=1,
        context=8192,
        scenario={"id": "project-intake-analysis"},
        thinking_mode="off",
        status="COMPLETE",
        result={
            "output": output,
            "first_generation_ms": 10.0,
            "ttft_ms": 20.0,
            "wall_ms": 30.0,
            "eval_count": 42,
            "eval_duration_ns": 100,
            "tokens_per_second": 7.0,
            "load_duration_ns": 1,
            "prompt_eval_count": 2,
            "thinking_chars": 0,
            "done_reason": "stop",
            "output_truncated": False,
        },
        check_pass=True,
        check_details=["nonempty:pass"],
        error=None,
        ps_snapshot=None,
    )
    assert "output" not in record
    assert record["thinking_mode"] == "off"
    assert record["output_chars"] == len(output)
    assert record["output_sha256"] == hashlib.sha256(output.encode("utf-8")).hexdigest()
