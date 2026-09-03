from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import benchmark_local as core

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"
RESULTS = ROOT / "benchmarks" / "results"
QWEN_NATIVE_MAX_OUTPUT_TOKENS = 640


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qualification locale bornée à 40 minutes maximum."
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--max-wall-seconds", type=float, default=None)
    parser.add_argument("--case-timeout-seconds", type=float, default=None)
    return parser.parse_args()


def _runtime_budget(policy: dict[str, Any]) -> dict[str, float]:
    raw = policy.get("runtime_budget", {})
    return {
        "qualification": float(raw.get("qualification_max_wall_seconds", 2400)),
        "benchmark": float(raw.get("benchmark_default_max_wall_seconds", 2100)),
        "case": float(raw.get("max_case_wall_seconds", 150)),
    }


def _selected_models(
    catalog: dict[str, Any],
    policy: dict[str, Any],
    available: set[str],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for alias in policy["automated_gates"]["required_models"]:
        model = catalog.get("models", {}).get(alias)
        if not isinstance(model, dict):
            raise ValueError(f"alias modèle inconnu: {alias}")
        if model.get("provider") != "ollama":
            raise ValueError(
                f"{alias}: provider={model.get('provider')} non exécutable par le runner Ollama"
            )
        runtime_id = str(model["runtime_id"])
        if not core.model_available(runtime_id, available):
            missing.append(f"{alias} ({runtime_id})")
        selected.append({"alias": alias, **model})
    if missing:
        raise ValueError("modèles absents dans Ollama: " + ", ".join(missing))
    return selected


def _matrix_plan(
    policy: dict[str, Any],
    suite: dict[str, Any],
    selected_models: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], int, dict[str, Any]]]:
    scenarios = {str(item["id"]): item for item in suite["scenarios"]}
    matrix = policy["automated_gates"].get("scenario_matrix")
    if not isinstance(matrix, dict):
        raise ValueError("scenario_matrix absente de qualification_policy.yaml")

    required_contexts = [int(value) for value in policy["required_contexts"]]
    plan: list[tuple[dict[str, Any], int, dict[str, Any]]] = []
    covered_baseline: set[str] = set()
    baseline = min(required_contexts)

    for model in selected_models:
        alias = str(model["alias"])
        model_matrix = matrix.get(alias)
        if not isinstance(model_matrix, dict):
            raise ValueError(f"scenario_matrix absente pour {alias}")
        for context in required_contexts:
            ids = model_matrix.get(str(context))
            if not isinstance(ids, list) or not ids:
                raise ValueError(f"scenario_matrix {alias}/{context} vide ou absente")
            if len(ids) != len(set(str(value) for value in ids)):
                raise ValueError(f"scenario_matrix {alias}/{context} contient des doublons")
            for scenario_id_raw in ids:
                scenario_id = str(scenario_id_raw)
                scenario = scenarios.get(scenario_id)
                if scenario is None:
                    raise ValueError(
                        f"scenario_matrix {alias}/{context}: scénario inconnu {scenario_id}"
                    )
                plan.append((model, context, scenario))
                if context == baseline:
                    covered_baseline.add(scenario_id)

    expected_scenarios = set(scenarios)
    if covered_baseline != expected_scenarios:
        missing = sorted(expected_scenarios - covered_baseline)
        extra = sorted(covered_baseline - expected_scenarios)
        raise ValueError(
            f"couverture 8K incomplète: missing={missing} extra={extra}"
        )

    return plan


def _qwen_native_case(
    alias: str,
    context: int,
    scenario_id: str,
    policy: dict[str, Any],
) -> bool:
    if alias != "qwen-max":
        return False
    configured = {
        str(value)
        for value in policy["automated_gates"].get("qwen_native_cases", [])
    }
    return f"{context}:{scenario_id}" in configured


def _generation_policy(
    model: dict[str, Any],
    context: int,
    scenario_id: str,
    scenario_limit: int,
    policy: dict[str, Any],
) -> tuple[int, bool | None, str]:
    family = str(model.get("family") or "").casefold()
    alias = str(model["alias"])
    if family == "gemma":
        return scenario_limit, False, "off"
    if family == "qwen":
        if _qwen_native_case(alias, context, scenario_id, policy):
            return max(scenario_limit, QWEN_NATIVE_MAX_OUTPUT_TOKENS), None, "native"
        return scenario_limit, False, "off"
    return scenario_limit, None, "not_applicable"


def run_generation_bounded(
    endpoint: str,
    runtime_id: str,
    prompt: str,
    context: int,
    temperature: float,
    num_predict: int,
    *,
    think: bool | None,
    deadline: float,
) -> dict[str, Any]:
    now = time.perf_counter()
    remaining = deadline - now
    if remaining <= 0:
        raise TimeoutError("budget mural du cas épuisé avant l'appel")

    body = json.dumps(
        core.generation_payload(
            runtime_id,
            prompt,
            context,
            temperature,
            num_predict,
            think,
        )
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{endpoint}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    first_generated_at: float | None = None
    first_response_at: float | None = None
    chunks: list[str] = []
    thinking_chars = 0
    final: dict[str, Any] = {}

    with urllib.request.urlopen(  # noqa: S310
        request,
        timeout=max(1.0, remaining),
    ) as response:
        for raw_line in response:
            if time.perf_counter() >= deadline:
                raise TimeoutError("timeout mural du cas atteint")
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            event = json.loads(line)
            message = event.get("message")
            if not isinstance(message, dict):
                message = {}
            thinking_chunk = str(message.get("thinking", ""))
            response_chunk = str(message.get("content", ""))
            if (thinking_chunk or response_chunk) and first_generated_at is None:
                first_generated_at = time.perf_counter()
            if response_chunk and first_response_at is None:
                first_response_at = time.perf_counter()
            thinking_chars += len(thinking_chunk)
            chunks.append(response_chunk)
            if event.get("done"):
                final = event

    ended = time.perf_counter()
    if ended > deadline:
        raise TimeoutError("timeout mural du cas atteint")

    eval_count = int(final.get("eval_count") or 0)
    eval_duration = int(final.get("eval_duration") or 0)
    tokens_per_second = (
        eval_count / eval_duration * 1_000_000_000 if eval_duration else None
    )
    done_reason = str(final.get("done_reason") or "") or None
    limit_reason = bool(
        done_reason and done_reason.casefold() in {"length", "max_tokens", "limit"}
    )
    output_truncated = limit_reason or eval_count >= num_predict

    return {
        "output": "".join(chunks).strip(),
        "first_generation_ms": (
            (first_generated_at - started) * 1000 if first_generated_at else None
        ),
        "ttft_ms": (
            (first_response_at - started) * 1000 if first_response_at else None
        ),
        "wall_ms": (ended - started) * 1000,
        "eval_count": eval_count,
        "eval_duration_ns": eval_duration,
        "tokens_per_second": tokens_per_second,
        "load_duration_ns": int(final.get("load_duration") or 0),
        "prompt_eval_count": int(final.get("prompt_eval_count") or 0),
        "thinking_chars": thinking_chars,
        "done_reason": done_reason,
        "output_truncated": output_truncated,
    }


def _metric(value: object, *, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _write_evidence(
    *,
    suite: dict[str, Any],
    policy: dict[str, Any],
    version: dict[str, Any],
    models: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    started_at: datetime,
    run_started: float,
    max_wall_seconds: float,
    case_timeout_seconds: float,
    budget_exhausted: bool,
) -> Path:
    finished_at = datetime.now(UTC)
    total_wall_ms = (time.perf_counter() - run_started) * 1000
    payload = {
        "schema_version": "1.4.0",
        "protocol": "qualification-hard-40m-v1",
        "suite": suite["id"],
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "ollama_version": version.get("version"),
        "max_wall_seconds": max_wall_seconds,
        "case_timeout_seconds": case_timeout_seconds,
        "budget_exhausted": budget_exhausted,
        "required_contexts": policy["required_contexts"],
        "scenario_matrix": policy["automated_gates"]["scenario_matrix"],
        "qwen_native_cases": policy["automated_gates"].get("qwen_native_cases", []),
        "total_wall_ms": total_wall_ms,
        "models": [
            {
                "alias": model["alias"],
                "runtime_id": model["runtime_id"],
                "family": model.get("family"),
                "class": model.get("class"),
                "status": model.get("status"),
            }
            for model in models
        ],
        "cases": cases,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"benchmark_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    catalog = core.load_yaml(CONFIG / "model_catalog.yaml")
    policy = core.load_yaml(CONFIG / "qualification_policy.yaml")
    suite_id = str(policy["suite"])
    suite = core.load_yaml(core.suite_path(suite_id))
    if str(suite.get("id")) != suite_id:
        print(f"KO  suite incohérente: attendu {suite_id}, reçu {suite.get('id')}")
        return 2

    budget = _runtime_budget(policy)
    max_wall_seconds = (
        float(args.max_wall_seconds)
        if args.max_wall_seconds is not None
        else budget["benchmark"]
    )
    max_wall_seconds = min(max_wall_seconds, budget["qualification"])
    case_timeout_seconds = (
        float(args.case_timeout_seconds)
        if args.case_timeout_seconds is not None
        else budget["case"]
    )
    case_timeout_seconds = min(case_timeout_seconds, budget["case"])
    if max_wall_seconds <= 0 or case_timeout_seconds <= 0:
        print("KO  budgets de temps invalides")
        return 2

    try:
        tags = core.request_json(f"{args.endpoint}/api/tags")
        version = core.request_json(f"{args.endpoint}/api/version")
        available = {
            str(item.get("name") or item.get("model"))
            for item in tags.get("models", [])
            if item.get("name") or item.get("model")
        }
        models = _selected_models(catalog, policy, available)
        plan = _matrix_plan(policy, suite, models)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"KO  préflight qualification: {exc}")
        return 2

    limits = {
        str(item["id"]): core.scenario_output_limit(item, suite)
        for item in suite["scenarios"]
    }
    contexts = [int(value) for value in policy["required_contexts"]]
    context_counts = {
        context: sum(1 for _, item_context, _ in plan if item_context == context)
        for context in contexts
    }
    native_count = sum(
        1
        for model, context, scenario in plan
        if _qwen_native_case(
            str(model["alias"]), context, str(scenario["id"]), policy
        )
    )

    started_at = datetime.now(UTC)
    run_started = time.perf_counter()
    deadline = run_started + max_wall_seconds
    cases: list[dict[str, Any]] = []
    budget_exhausted = False

    context_plan = ",".join(
        f"{context}:{context_counts[context]}" for context in contexts
    )
    print(
        "BENCHMARK_PLAN "
        f"modeles={len(models)} cas={len(plan)} context_cases={context_plan} "
        f"qwen_native_probes={native_count} qwen_native_max={QWEN_NATIVE_MAX_OUTPUT_TOKENS} "
        f"hard_wall={int(max_wall_seconds)}s case_timeout={int(case_timeout_seconds)}s"
    )

    for current, (model, context, scenario) in enumerate(plan, start=1):
        now = time.perf_counter()
        remaining_global = deadline - now
        if remaining_global <= 0:
            budget_exhausted = True
            print("HARD_TIMEOUT budget global du benchmark épuisé")
            break

        alias = str(model["alias"])
        runtime_id = str(model["runtime_id"])
        scenario_id = str(scenario["id"])
        scenario_limit = limits[scenario_id]
        max_output_tokens, think, thinking_mode = _generation_policy(
            model,
            context,
            scenario_id,
            scenario_limit,
            policy,
        )
        prompt = core.add_synthetic_context(
            str(scenario["prompt"]),
            int(scenario.get("synthetic_context_chars") or 0),
        )
        case_deadline = min(deadline, now + case_timeout_seconds)

        print(
            f"[{current}/{len(plan)}] {alias} ctx={context} scenario={scenario_id} "
            f"max_out={max_output_tokens} thinking={thinking_mode} "
            f"budget_left={core.format_duration(remaining_global)}"
        )
        base = {
            "model_alias": alias,
            "runtime_id": runtime_id,
            "context": context,
            "scenario_id": scenario_id,
            "category": scenario.get("category"),
            "scenario_max_output_tokens": scenario_limit,
            "max_output_tokens": max_output_tokens,
            "thinking_mode": thinking_mode,
            "check_required": True,
        }

        try:
            result = run_generation_bounded(
                args.endpoint,
                runtime_id,
                prompt,
                context,
                float(scenario.get("temperature", suite["default_temperature"])),
                max_output_tokens,
                think=think,
                deadline=case_deadline,
            )
            first_token_ms = (
                result["first_generation_ms"]
                if thinking_mode == "native"
                else result["ttft_ms"]
            )
            passed, details = core.run_checks(
                result["output"], list(scenario.get("checks", []))
            )
            case_status = "ok"
            if result["output_truncated"]:
                passed = False
                case_status = "error"
                details.append("output_limit:fail")

            cases.append(
                {
                    **base,
                    **result,
                    "first_token_ms": first_token_ms,
                    "status": case_status,
                    "check_passed": passed,
                    "check_details": details,
                }
            )
            elapsed = time.perf_counter() - run_started
            average = elapsed / current
            eta = average * (len(plan) - current)
            verdict = "PASS" if passed else "CHECK_FAIL"
            limit_flag = " LIMIT" if result["output_truncated"] else ""
            print(
                f"    {verdict}{limit_flag} wall={result['wall_ms'] / 1000:.1f}s "
                f"first_tok={_metric(first_token_ms, digits=0)}ms "
                f"response_ttft={_metric(result['ttft_ms'], digits=0)}ms "
                f"tok/s={_metric(result['tokens_per_second'])} out={result['eval_count']} "
                f"think_chars={result['thinking_chars']} reste~{core.format_duration(eta)}"
            )
            if result["output_truncated"]:
                print("FAIL_FAST sortie tronquée: max_error_rate=0, qualification impossible")
                path = _write_evidence(
                    suite=suite,
                    policy=policy,
                    version=version,
                    models=models,
                    cases=cases,
                    started_at=started_at,
                    run_started=run_started,
                    max_wall_seconds=max_wall_seconds,
                    case_timeout_seconds=case_timeout_seconds,
                    budget_exhausted=False,
                )
                print(f"EVIDENCE={path}")
                return 2
        except (
            OSError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            cases.append(
                {
                    **base,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "check_passed": False,
                }
            )
            print(f"    ERROR {type(exc).__name__}: {exc}")
            print("FAIL_FAST erreur API/timeout: max_error_rate=0, qualification impossible")
            if time.perf_counter() >= deadline:
                budget_exhausted = True
            path = _write_evidence(
                suite=suite,
                policy=policy,
                version=version,
                models=models,
                cases=cases,
                started_at=started_at,
                run_started=run_started,
                max_wall_seconds=max_wall_seconds,
                case_timeout_seconds=case_timeout_seconds,
                budget_exhausted=budget_exhausted,
            )
            print(f"EVIDENCE={path}")
            return 2

    path = _write_evidence(
        suite=suite,
        policy=policy,
        version=version,
        models=models,
        cases=cases,
        started_at=started_at,
        run_started=run_started,
        max_wall_seconds=max_wall_seconds,
        case_timeout_seconds=case_timeout_seconds,
        budget_exhausted=budget_exhausted,
    )
    total_wall = time.perf_counter() - run_started
    errors = sum(case.get("status") != "ok" for case in cases)
    checks = sum(case.get("check_passed") is True for case in cases)
    print(f"EVIDENCE={path}")
    print(
        f"CAS={len(cases)}/{len(plan)} CHECKS_OK={checks} ERREURS={errors} "
        f"DUREE={core.format_duration(total_wall)} BUDGET={core.format_duration(max_wall_seconds)}"
    )

    if budget_exhausted or len(cases) != len(plan):
        print("KO  HARD_TIMEOUT qualification benchmark > budget autorisé")
        return 2
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
