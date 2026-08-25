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


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML invalide: {path}")
    return data


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


def run_checks(output: str, checks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    details: list[str] = []
    cleaned = strip_fence(output)
    overall = True
    for check in checks:
        check_type = check["type"]
        passed = False
        if check_type == "nonempty":
            passed = bool(cleaned.strip())
        elif check_type == "contains_any":
            lowered = cleaned.casefold()
            passed = any(
                str(value).casefold() in lowered for value in check.get("values", [])
            )
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
    while sum(len(row) + 1 for row in rows) < target_chars:
        rows.append(
            f"service-{index:04d}: namespace=dev; replicas=2; image=example/app:{index % 7}; "
            f"owner=team-{index % 5}; drift={'yes' if index % 11 == 0 else 'no'}"
        )
        index += 1
    return "INVENTAIRE SYNTHÉTIQUE:\n" + "\n".join(rows) + "\n\nCONSIGNE:\n" + prompt


def run_generation(
    endpoint: str,
    runtime_id: str,
    prompt: str,
    context: int,
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": runtime_id,
            "prompt": prompt,
            "stream": True,
            "options": {"num_ctx": context, "temperature": temperature},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{endpoint}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    first_token_at: float | None = None
    chunks: list[str] = []
    final: dict[str, Any] = {}
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            event = json.loads(line)
            chunk = str(event.get("response", ""))
            if chunk and first_token_at is None:
                first_token_at = time.perf_counter()
            chunks.append(chunk)
            if event.get("done"):
                final = event
    ended = time.perf_counter()
    eval_count = int(final.get("eval_count") or 0)
    eval_duration = int(final.get("eval_duration") or 0)
    tokens_per_second = (eval_count / eval_duration * 1_000_000_000) if eval_duration else None
    return {
        "output": "".join(chunks).strip(),
        "ttft_ms": (first_token_at - started) * 1000 if first_token_at else None,
        "wall_ms": (ended - started) * 1000,
        "eval_count": eval_count,
        "eval_duration_ns": eval_duration,
        "tokens_per_second": tokens_per_second,
        "load_duration_ns": int(final.get("load_duration") or 0),
        "prompt_eval_count": int(final.get("prompt_eval_count") or 0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark local reproductible via API native Ollama."
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--context", action="append", type=int, dest="contexts")
    parser.add_argument("--include-specialist", action="store_true")
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = load_yaml(CONFIG / "model_catalog.yaml")
    policy = load_yaml(CONFIG / "qualification_policy.yaml")
    suite = load_yaml(ROOT / "benchmarks" / "suites" / "devops_v1.yaml")
    aliases = args.models or list(policy["automated_gates"]["required_models"])
    if args.include_specialist:
        aliases.append("sera-devops")
    aliases = list(dict.fromkeys(aliases))
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
        if not model:
            print(f"KO  alias modèle inconnu: {alias}")
            return 2
        runtime_id = str(model["runtime_id"])
        if not model_available(runtime_id, available):
            missing.append(f"{alias} ({runtime_id})")
        selected_models.append({"alias": alias, **model})
    if missing:
        print("KO  modèles absents dans Ollama: " + ", ".join(missing))
        return 2

    started_at = datetime.now(UTC)
    cases: list[dict[str, Any]] = []
    total = len(selected_models) * len(contexts) * len(suite["scenarios"])
    current = 0
    for model in selected_models:
        for context in contexts:
            for scenario in suite["scenarios"]:
                current += 1
                alias = str(model["alias"])
                runtime_id = str(model["runtime_id"])
                scenario_id = str(scenario["id"])
                prompt = add_synthetic_context(
                    str(scenario["prompt"]),
                    int(scenario.get("synthetic_context_chars") or 0),
                )
                print(f"[{current}/{total}] {alias} ctx={context} scenario={scenario_id}")
                base = {
                    "model_alias": alias,
                    "runtime_id": runtime_id,
                    "context": context,
                    "scenario_id": scenario_id,
                    "category": scenario.get("category"),
                    "check_required": True,
                }
                try:
                    result = run_generation(
                        args.endpoint,
                        runtime_id,
                        prompt,
                        context,
                        float(scenario.get("temperature", suite["default_temperature"])),
                        args.timeout,
                    )
                    passed, details = run_checks(
                        result["output"], list(scenario.get("checks", []))
                    )
                    cases.append(
                        {
                            **base,
                            **result,
                            "status": "ok",
                            "check_passed": passed,
                            "check_details": details,
                        }
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

    RESULTS.mkdir(parents=True, exist_ok=True)
    finished_at = datetime.now(UTC)
    payload = {
        "schema_version": "1.0.0",
        "suite": suite["id"],
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "endpoint": args.endpoint,
        "ollama_version": version.get("version"),
        "contexts": contexts,
        "models": [
            {
                "alias": model["alias"],
                "runtime_id": model["runtime_id"],
                "family": model.get("family"),
                "status": model.get("status"),
            }
            for model in selected_models
        ],
        "cases": cases,
    }
    path = RESULTS / f"benchmark_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = sum(case["status"] != "ok" for case in cases)
    checks = sum(case.get("check_passed") is True for case in cases)
    print(f"EVIDENCE={path}")
    print(f"CAS={len(cases)} CHECKS_OK={checks} ERREURS={errors}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
