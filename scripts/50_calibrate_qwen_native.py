from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import benchmark_local as core
import benchmark_qualification_40m as hard40

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"
RESULTS = ROOT / "benchmarks" / "results"
QWEN_ALIAS = "qwen-max"
DEFAULT_MAX_OUTPUT_TOKENS = 1536
DEFAULT_CASE_TIMEOUT_SECONDS = 480.0
DEFAULT_THINKING_MODE = "native"
THINKING_MODES = ("native", "off")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calibre les probes Qwen avec thinking natif ou désactivé "
            "sans promouvoir la qualification."
        )
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=DEFAULT_MAX_OUTPUT_TOKENS,
    )
    parser.add_argument(
        "--case-timeout-seconds",
        type=float,
        default=DEFAULT_CASE_TIMEOUT_SECONDS,
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--thinking-mode",
        choices=THINKING_MODES,
        default=DEFAULT_THINKING_MODE,
        help="native conserve le reasoning Ollama/Qwen; off envoie think=false.",
    )
    return parser.parse_args()


def _native_plan(
    policy: dict[str, Any],
    suite: dict[str, Any],
) -> list[tuple[int, dict[str, Any]]]:
    scenarios = {str(item["id"]): item for item in suite["scenarios"]}
    plan: list[tuple[int, dict[str, Any]]] = []
    configured = policy["automated_gates"].get("qwen_native_cases", [])
    if not isinstance(configured, list) or not configured:
        raise ValueError("qwen_native_cases absent ou vide")

    for raw in configured:
        value = str(raw)
        context_raw, separator, scenario_id = value.partition(":")
        if not separator:
            raise ValueError(f"qwen_native_cases invalide: {value}")
        context = int(context_raw)
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            raise ValueError(f"scénario Qwen natif inconnu: {scenario_id}")
        plan.append((context, scenario))
    return plan


def _thinking_value(mode: str) -> bool | None:
    if mode == "native":
        return None
    if mode == "off":
        return False
    raise ValueError(f"thinking-mode invalide: {mode}")


def _ollama_ps_snapshot(endpoint: str, runtime_id: str) -> dict[str, Any] | None:
    try:
        payload = core.request_json(f"{endpoint}/api/ps")
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None

    for item in payload.get("models", []):
        name = str(item.get("name") or item.get("model") or "")
        if not core.model_available(runtime_id, {name}):
            continue
        return {
            "name": name,
            "size": item.get("size"),
            "size_vram": item.get("size_vram"),
            "context_length": item.get("context_length"),
            "expires_at": item.get("expires_at"),
        }
    return None


def _case_record(
    *,
    repeat: int,
    context: int,
    scenario: dict[str, Any],
    thinking_mode: str,
    status: str,
    result: dict[str, Any] | None,
    check_pass: bool | None,
    check_details: list[str],
    error: str | None,
    ps_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "repeat": repeat,
        "context": context,
        "scenario_id": str(scenario["id"]),
        "thinking_mode": thinking_mode,
        "status": status,
        "check_pass": check_pass,
        "check_details": check_details,
        "error": error,
        "ollama_ps": ps_snapshot,
    }
    if result is None:
        return record

    output = str(result.get("output") or "")
    record.update(
        {
            "first_generation_ms": result.get("first_generation_ms"),
            "ttft_ms": result.get("ttft_ms"),
            "wall_ms": result.get("wall_ms"),
            "eval_count": result.get("eval_count"),
            "eval_duration_ns": result.get("eval_duration_ns"),
            "tokens_per_second": result.get("tokens_per_second"),
            "load_duration_ns": result.get("load_duration_ns"),
            "prompt_eval_count": result.get("prompt_eval_count"),
            "thinking_chars": result.get("thinking_chars"),
            "done_reason": result.get("done_reason"),
            "output_truncated": result.get("output_truncated"),
            "output_chars": len(output),
            "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        }
    )
    return record


def _write_evidence(
    *,
    runtime_id: str,
    thinking_mode: str,
    max_output_tokens: int,
    case_timeout_seconds: float,
    repeats: int,
    started_at: datetime,
    cases: list[dict[str, Any]],
) -> Path:
    finished_at = datetime.now(UTC)
    statuses = [str(item["status"]) for item in cases]
    complete = bool(cases) and all(status == "COMPLETE" for status in statuses)
    payload = {
        "schema_version": "1.1.0",
        "protocol": "qwen-thinking-calibration-v2",
        "qualification_effect": "none",
        "promotion_allowed": False,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "model_alias": QWEN_ALIAS,
        "runtime_id": runtime_id,
        "thinking_mode": thinking_mode,
        "max_output_tokens": max_output_tokens,
        "case_timeout_seconds": case_timeout_seconds,
        "repeats": repeats,
        "result": "COMPLETE" if complete else "MEASURED_WITH_LIMITS",
        "cases": cases,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = finished_at.strftime("%Y%m%d_%H%M%S")
    path = RESULTS / f"qwen_thinking_calibration_{thinking_mode}_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    if args.max_output_tokens <= 0 or args.max_output_tokens > core.MAX_CONFIGURED_OUTPUT_TOKENS:
        print(
            "KO  max-output-tokens hors plage: "
            f"1..{core.MAX_CONFIGURED_OUTPUT_TOKENS} attendu"
        )
        return 2
    if args.case_timeout_seconds <= 0:
        print("KO  case-timeout-seconds doit être > 0")
        return 2
    if args.repeats <= 0 or args.repeats > 3:
        print("KO  repeats doit être compris entre 1 et 3")
        return 2

    catalog = core.load_yaml(CONFIG / "model_catalog.yaml")
    policy = core.load_yaml(CONFIG / "qualification_policy.yaml")
    suite = core.load_yaml(core.suite_path(str(policy["suite"])))
    model = catalog.get("models", {}).get(QWEN_ALIAS)
    if not isinstance(model, dict) or model.get("provider") != "ollama":
        print("KO  qwen-max absent ou non routé vers Ollama")
        return 2
    runtime_id = str(model["runtime_id"])

    try:
        tags = core.request_json(f"{args.endpoint}/api/tags")
        available = {
            str(item.get("name") or item.get("model"))
            for item in tags.get("models", [])
            if item.get("name") or item.get("model")
        }
        if not core.model_available(runtime_id, available):
            print(f"KO  modèle absent dans Ollama: {runtime_id}")
            return 2
        plan = _native_plan(policy, suite)
        think_value = _thinking_value(str(args.thinking_mode))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"KO  préflight calibration: {exc}")
        return 2

    started_at = datetime.now(UTC)
    cases: list[dict[str, Any]] = []
    total = len(plan) * args.repeats
    current = 0
    print(
        "QWEN_THINKING_CALIBRATION "
        f"probes={len(plan)} repeats={args.repeats} cases={total} "
        f"thinking={args.thinking_mode} max_out={args.max_output_tokens} "
        f"timeout={int(args.case_timeout_seconds)}s qualification_effect=none"
    )

    for repeat in range(1, args.repeats + 1):
        for context, scenario in plan:
            current += 1
            scenario_id = str(scenario["id"])
            prompt = core.add_synthetic_context(
                str(scenario["prompt"]),
                int(scenario.get("synthetic_context_chars") or 0),
            )
            print(
                f"[{current}/{total}] repeat={repeat} ctx={context} "
                f"scenario={scenario_id} thinking={args.thinking_mode}"
            )
            result: dict[str, Any] | None = None
            check_pass: bool | None = None
            check_details: list[str] = []
            error: str | None = None
            status = "ERROR"
            started = time.perf_counter()
            deadline = started + args.case_timeout_seconds
            try:
                result = hard40.run_generation_bounded(
                    args.endpoint,
                    runtime_id,
                    prompt,
                    context,
                    float(scenario.get("temperature", suite["default_temperature"])),
                    args.max_output_tokens,
                    think=think_value,
                    deadline=deadline,
                )
                check_pass, check_details = core.run_checks(
                    str(result["output"]),
                    list(scenario.get("checks", [])),
                )
                if result["output_truncated"]:
                    status = "TRUNCATED"
                elif check_pass:
                    status = "COMPLETE"
                else:
                    status = "CHECK_FAIL"
            except TimeoutError as exc:
                status = "TIMEOUT"
                error = str(exc)
            except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
                status = "ERROR"
                error = f"{type(exc).__name__}: {exc}"

            ps_snapshot = _ollama_ps_snapshot(args.endpoint, runtime_id)
            record = _case_record(
                repeat=repeat,
                context=context,
                scenario=scenario,
                thinking_mode=str(args.thinking_mode),
                status=status,
                result=result,
                check_pass=check_pass,
                check_details=check_details,
                error=error,
                ps_snapshot=ps_snapshot,
            )
            cases.append(record)
            if result is None:
                wall_seconds = time.perf_counter() - started
                print(f"    {status} wall={wall_seconds:.1f}s error={error}")
            else:
                print(
                    f"    {status} wall={float(result['wall_ms']) / 1000:.1f}s "
                    f"first_tok={result['first_generation_ms']:.0f}ms "
                    f"tok/s={result['tokens_per_second']:.1f} "
                    f"out={result['eval_count']} think_chars={result['thinking_chars']}"
                )

    path = _write_evidence(
        runtime_id=runtime_id,
        thinking_mode=str(args.thinking_mode),
        max_output_tokens=args.max_output_tokens,
        case_timeout_seconds=args.case_timeout_seconds,
        repeats=args.repeats,
        started_at=started_at,
        cases=cases,
    )
    complete = all(str(item["status"]) == "COMPLETE" for item in cases)
    print(f"CALIBRATION_RESULT={'COMPLETE' if complete else 'MEASURED_WITH_LIMITS'}")
    print(f"EVIDENCE={path}")
    print("INFO  Aucune qualification, identité modèle ou promotion backend n'a été modifiée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
