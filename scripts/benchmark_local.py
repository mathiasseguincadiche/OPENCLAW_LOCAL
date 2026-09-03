from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"
RESULTS = ROOT / "benchmarks" / "results"
DEFAULT_MAX_OUTPUT_TOKENS = 512
MAX_CONFIGURED_OUTPUT_TOKENS = 2048


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML invalide: {path}")
    return data


def suite_path(suite_id: str) -> Path:
    candidates = (
        ROOT / "benchmarks" / "suites" / f"{suite_id}.yaml",
        ROOT / "benchmarks" / "suites" / f"{suite_id.replace('-', '_')}.yaml",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"suite de benchmark introuvable: {suite_id}")


def request_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def model_available(runtime_id: str, names: set[str]) -> bool:
    if runtime_id in names:
        return True
    if ":" not in runtime_id:
        return any(
            name == f"{runtime_id}:latest" or name.startswith(f"{runtime_id}:")
            for name in names
        )
    return False


def strip_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return value


def _contains(cleaned: str, values: list[object], *, require_all: bool) -> bool:
    lowered = cleaned.casefold()
    matches = [str(value).casefold() in lowered for value in values]
    return all(matches) if require_all else any(matches)


def run_checks(output: str, checks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    details: list[str] = []
    cleaned = strip_fence(output)
    overall = True
    for check in checks:
        check_type = str(check["type"])
        values = list(check.get("values", []))
        passed = False

        if check_type == "nonempty":
            passed = bool(cleaned.strip())
        elif check_type == "contains_any":
            passed = _contains(cleaned, values, require_all=False)
        elif check_type == "contains_all":
            passed = _contains(cleaned, values, require_all=True)
        elif check_type == "not_contains_any":
            passed = not _contains(cleaned, values, require_all=False)
        elif check_type == "json_keys":
            try:
                parsed = json.loads(cleaned)
                passed = isinstance(parsed, dict) and all(
                    key in parsed for key in check.get("keys", [])
                )
            except json.JSONDecodeError:
                passed = False
        elif check_type == "yaml_keys":
            try:
                parsed = yaml.safe_load(cleaned)
                passed = isinstance(parsed, dict) and all(
                    key in parsed for key in check.get("keys", [])
                )
            except yaml.YAMLError:
                passed = False
        else:
            raise ValueError(f"Type de contrôle inconnu: {check_type}")

        overall = overall and passed
        details.append(f"{check_type}:{'pass' if passed else 'fail'}")
    return overall, details


def add_synthetic_context(prompt: str, target_chars: int) -> str:
    if target_chars <= 0:
        return prompt
    rows: list[str] = []
    index = 1
    current_chars = 0
    while current_chars < target_chars:
        row = (
            f"service-{index:04d}: namespace=dev; replicas=2; "
            f"image=example/app:{index % 7}; owner=team-{index % 5}; "
            f"drift={'yes' if index % 11 == 0 else 'no'}"
        )
        rows.append(row)
        current_chars += len(row) + 1
        index += 1
    return "INVENTAIRE SYNTHÉTIQUE:\n" + "\n".join(rows) + "\n\nCONSIGNE:\n" + prompt


def scenario_output_limit(
    scenario: dict[str, Any],
    suite: dict[str, Any],
) -> int:
    raw = scenario.get(
        "max_output_tokens",
        suite.get("default_max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS),
    )
    try:
        limit = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"max_output_tokens invalide pour {scenario.get('id', '<inconnu>')}: {raw!r}"
        ) from exc
    if limit <= 0 or limit > MAX_CONFIGURED_OUTPUT_TOKENS:
        raise ValueError(
            f"max_output_tokens hors plage pour {scenario.get('id', '<inconnu>')}: "
            f"{limit} (attendu 1..{MAX_CONFIGURED_OUTPUT_TOKENS})"
        )
    return limit


def resolve_generation_policy(
    model: dict[str, Any],
    scenario_limit: int,
    qwen_thinking: str,
) -> tuple[int, bool | None, str]:
    family = str(model.get("family") or "").casefold()
    if family == "gemma":
        # Les gates fonctionnels bornent la réponse finale. Gemma 4 possède désormais
        # un canal thinking configurable qui peut consommer ce budget avant content.
        # Le raisonnement profond reste couvert par les E2E/projets représentatifs.
        return scenario_limit, False, "off"
    if family != "qwen":
        return scenario_limit, None, "not_applicable"
    if qwen_thinking == "off":
        return scenario_limit, False, "off"
    return MAX_CONFIGURED_OUTPUT_TOKENS, None, "native"


def generation_payload(
    runtime_id: str,
    prompt: str,
    context: int,
    temperature: float,
    num_predict: int,
    think: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": runtime_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "keep_alive": "15m",
        "options": {
            "num_ctx": context,
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }
    if think is not None:
        payload["think"] = think
    return payload


def run_generation(
    endpoint: str,
    runtime_id: str,
    prompt: str,
    context: int,
    temperature: float,
    num_predict: int,
    timeout: float,
    *,
    think: bool | None,
) -> dict[str, Any]:
    body = json.dumps(
        generation_payload(
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

    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        for raw_line in response:
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


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}h{minutes:02d}m{secs:02d}s"
    if minutes:
        return f"{minutes:d}m{secs:02d}s"
    return f"{secs:d}s"


def _metric(value: object, *, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark local reproductible via API chat native Ollama."
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Override de diagnostic; sans option, les trois modèles required sont benchmarkés.",
    )
    parser.add_argument("--context", action="append", type=int, dest="contexts")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--qwen-thinking",
        choices=("native", "off"),
        default="native",
        help=(
            "Politique Qwen: native conserve le thinking du modèle; "
            "off le désactive pour les passes rapides."
        ),
    )
    return parser.parse_args()


def _selected_aliases(
    args: argparse.Namespace,
    policy: dict[str, Any],
) -> list[str]:
    aliases = list(args.models or policy["automated_gates"]["required_models"])
    return list(dict.fromkeys(str(alias) for alias in aliases))


def main() -> int:
    args = parse_args()
    catalog = load_yaml(CONFIG / "model_catalog.yaml")
    policy = load_yaml(CONFIG / "qualification_policy.yaml")
    suite_id = str(policy["suite"])
    suite = load_yaml(suite_path(suite_id))

    if str(suite.get("id")) != suite_id:
        print(f"KO  suite incohérente: attendu {suite_id}, reçu {suite.get('id')}")
        return 2

    aliases = _selected_aliases(args, policy)
    contexts = args.contexts or [int(value) for value in policy["required_contexts"]]

    try:
        tags = request_json(f"{args.endpoint}/api/tags")
        version = request_json(f"{args.endpoint}/api/version")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"KO  Ollama inaccessible: {exc}")
        return 2

    available = {
        str(item.get("name") or item.get("model"))
        for item in tags.get("models", [])
        if item.get("name") or item.get("model")
    }
    missing: list[str] = []
    selected_models: list[dict[str, Any]] = []

    for alias in aliases:
        model = catalog["models"].get(alias)
        if not isinstance(model, dict):
            print(f"KO  alias modèle inconnu: {alias}")
            return 2
        if model.get("provider") != "ollama":
            print(
                f"KO  {alias}: provider={model.get('provider')} non exécutable "
                "par le runner Ollama"
            )
            return 2
        runtime_id = str(model["runtime_id"])
        if not model_available(runtime_id, available):
            missing.append(f"{alias} ({runtime_id})")
        selected_models.append({"alias": alias, **model})

    if missing:
        print("KO  modèles absents dans Ollama: " + ", ".join(missing))
        return 2

    scenarios = list(suite["scenarios"])
    try:
        limits = {str(item["id"]): scenario_output_limit(item, suite) for item in scenarios}
    except ValueError as exc:
        print(f"KO  configuration benchmark: {exc}")
        return 2

    started_at = datetime.now(UTC)
    run_started = time.perf_counter()
    cases: list[dict[str, Any]] = []
    total = len(selected_models) * len(contexts) * len(scenarios)
    current = 0
    print(
        "BENCHMARK_PLAN "
        f"modeles={len(selected_models)} contextes={len(contexts)} "
        f"scenarios={len(scenarios)} cas={total} "
        f"qwen_thinking={args.qwen_thinking} gemma_thinking=off"
    )

    for model in selected_models:
        for context in contexts:
            for scenario in scenarios:
                current += 1
                alias = str(model["alias"])
                runtime_id = str(model["runtime_id"])
                scenario_id = str(scenario["id"])
                scenario_limit = limits[scenario_id]
                max_output_tokens, think, thinking_mode = resolve_generation_policy(
                    model,
                    scenario_limit,
                    args.qwen_thinking,
                )
                prompt = add_synthetic_context(
                    str(scenario["prompt"]),
                    int(scenario.get("synthetic_context_chars") or 0),
                )
                print(
                    f"[{current}/{total}] {alias} ctx={context} "
                    f"scenario={scenario_id} max_out={max_output_tokens} "
                    f"thinking={thinking_mode}"
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
                    result = run_generation(
                        args.endpoint,
                        runtime_id,
                        prompt,
                        context,
                        float(
                            scenario.get(
                                "temperature",
                                suite["default_temperature"],
                            )
                        ),
                        max_output_tokens,
                        args.timeout,
                        think=think,
                    )
                    passed, details = run_checks(
                        result["output"],
                        list(scenario.get("checks", [])),
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
                            "status": case_status,
                            "check_passed": passed,
                            "check_details": details,
                        }
                    )
                    elapsed = time.perf_counter() - run_started
                    average = elapsed / current
                    eta = average * (total - current)
                    verdict = "PASS" if passed else "CHECK_FAIL"
                    limit_flag = " LIMIT" if result["output_truncated"] else ""
                    print(
                        f"    {verdict}{limit_flag} "
                        f"wall={result['wall_ms'] / 1000:.1f}s "
                        f"ttft={_metric(result['ttft_ms'], digits=0)}ms "
                        f"tok/s={_metric(result['tokens_per_second'])} "
                        f"out={result['eval_count']} "
                        f"think_chars={result['thinking_chars']} "
                        f"reste~{format_duration(eta)}"
                    )
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
                    elapsed = time.perf_counter() - run_started
                    average = elapsed / current
                    eta = average * (total - current)
                    print(
                        f"    ERROR {type(exc).__name__}: {exc} "
                        f"reste~{format_duration(eta)}"
                    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    finished_at = datetime.now(UTC)
    total_wall_ms = (time.perf_counter() - run_started) * 1000
    payload = {
        "schema_version": "1.2.0",
        "suite": suite["id"],
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "endpoint": args.endpoint,
        "ollama_version": version.get("version"),
        "contexts": contexts,
        "qwen_thinking": args.qwen_thinking,
        "gemma_thinking": "off",
        "total_wall_ms": total_wall_ms,
        "models": [
            {
                "alias": model["alias"],
                "runtime_id": model["runtime_id"],
                "family": model.get("family"),
                "class": model.get("class"),
                "status": model.get("status"),
            }
            for model in selected_models
        ],
        "cases": cases,
    }
    path = RESULTS / f"benchmark_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    errors = sum(case["status"] != "ok" for case in cases)
    checks = sum(case.get("check_passed") is True for case in cases)
    print(f"EVIDENCE={path}")
    print(
        f"CAS={len(cases)} CHECKS_OK={checks} ERREURS={errors} "
        f"DUREE={format_duration(total_wall_ms / 1000)}"
    )
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
