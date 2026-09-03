from __future__ import annotations

import argparse
import hashlib
import json
import statistics
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
DEFAULT_ENDPOINT = "http://127.0.0.1:11434"

TOOL_INTENT_PROMPT = (
    "Tu dois inspecter config/prod.yaml. Utilise obligatoirement l'outil read_file "
    "avec path='config/prod.yaml'. Si l'outil signale file_not_found, ne devine pas: "
    "utilise list_files sur le répertoire config pour te réparer."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lire un fichier texte du workspace.",
            "parameters": {
                "type": "object",
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lister les fichiers d'un répertoire du workspace.",
            "parameters": {
                "type": "object",
                "required": ["directory"],
                "properties": {"directory": {"type": "string"}},
            },
        },
    },
]


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"YAML invalide: {path}")
    return value


def request_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"Réponse JSON invalide: {url}")
    return value


def post_chat(
    endpoint: str,
    payload: dict[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        f"{endpoint}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        value = json.load(response)
    wall_ms = (time.perf_counter() - started) * 1000
    if not isinstance(value, dict):
        raise ValueError("Réponse /api/chat non objet")
    return value, wall_ms


def model_available(runtime_id: str, names: set[str]) -> bool:
    if runtime_id in names:
        return True
    if ":" not in runtime_id:
        return any(
            name == f"{runtime_id}:latest" or name.startswith(f"{runtime_id}:")
            for name in names
        )
    return False


def tool_calls(message: object) -> list[dict[str, Any]]:
    if not isinstance(message, dict):
        return []
    raw = message.get("tool_calls", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def function_call(call: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    function = call.get("function", {})
    if not isinstance(function, dict):
        return "", {}
    arguments = function.get("arguments", {})
    if not isinstance(arguments, dict):
        arguments = {}
    return str(function.get("name") or ""), arguments


def has_tool_call(
    calls: list[dict[str, Any]],
    *,
    name: str,
    argument: str,
    expected: str,
) -> bool:
    expected_folded = expected.replace("\\", "/").rstrip("/").casefold()
    for call in calls:
        call_name, arguments = function_call(call)
        value = str(arguments.get(argument) or "")
        folded = value.replace("\\", "/").rstrip("/").casefold()
        if call_name == name and folded == expected_folded:
            return True
    return False


def response_fingerprint(response: dict[str, Any]) -> dict[str, Any]:
    message = response.get("message", {})
    if not isinstance(message, dict):
        message = {}
    content = str(message.get("content") or "")
    calls: list[dict[str, Any]] = []
    for item in tool_calls(message):
        name, arguments = function_call(item)
        calls.append({"name": name, "arguments": arguments})
    eval_count = int(response.get("eval_count") or 0)
    eval_duration = int(response.get("eval_duration") or 0)
    tokens_per_second = (
        eval_count / eval_duration * 1_000_000_000 if eval_duration > 0 else None
    )
    return {
        "content_chars": len(content),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "tool_calls": calls,
        "done_reason": str(response.get("done_reason") or "") or None,
        "eval_count": eval_count,
        "tokens_per_second": tokens_per_second,
    }


def assistant_message(response: dict[str, Any]) -> dict[str, Any]:
    raw = response.get("message", {})
    if not isinstance(raw, dict):
        return {"role": "assistant", "content": ""}
    message: dict[str, Any] = {
        "role": "assistant",
        "content": str(raw.get("content") or ""),
    }
    calls = tool_calls(raw)
    if calls:
        message["tool_calls"] = calls
    return message


def loaded_model_snapshot(endpoint: str, runtime_id: str) -> dict[str, Any] | None:
    try:
        payload = request_json(f"{endpoint}/api/ps")
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return None
    models = payload.get("models", [])
    if not isinstance(models, list):
        return None
    for item in models:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("model") or "")
        if name != runtime_id:
            continue
        size = int(item.get("size") or 0)
        size_vram = int(item.get("size_vram") or 0)
        return {
            "size_bytes": size,
            "size_vram_bytes": size_vram,
            "gpu_residency_ratio": size_vram / size if size > 0 else None,
            "context_length": int(item.get("context_length") or 0) or None,
        }
    return None


def chat_payload(
    runtime_id: str,
    messages: list[dict[str, Any]],
    context_tokens: int,
) -> dict[str, Any]:
    return {
        "model": runtime_id,
        "messages": messages,
        "tools": TOOLS,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "num_ctx": context_tokens,
            "temperature": 0,
            "num_predict": 256,
        },
    }


def run_iteration(
    endpoint: str,
    runtime_id: str,
    context_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": TOOL_INTENT_PROMPT}
    ]
    first, first_wall_ms = post_chat(
        endpoint,
        chat_payload(runtime_id, messages, context_tokens),
        timeout,
    )
    intent_pass = has_tool_call(
        tool_calls(first.get("message", {})),
        name="read_file",
        argument="path",
        expected="config/prod.yaml",
    )

    repair_pass = False
    second: dict[str, Any] | None = None
    repair_wall_ms: float | None = None
    if intent_pass:
        messages.extend(
            [
                assistant_message(first),
                {
                    "role": "tool",
                    "tool_name": "read_file",
                    "content": "ERROR file_not_found: config/prod.yaml",
                },
            ]
        )
        second, repair_wall_ms = post_chat(
            endpoint,
            chat_payload(runtime_id, messages, context_tokens),
            timeout,
        )
        repair_pass = has_tool_call(
            tool_calls(second.get("message", {})),
            name="list_files",
            argument="directory",
            expected="config",
        )

    return {
        "intent_pass": intent_pass,
        "repair_pass": repair_pass,
        "first_wall_ms": first_wall_ms,
        "repair_wall_ms": repair_wall_ms,
        "first_response": response_fingerprint(first),
        "repair_response": response_fingerprint(second) if second is not None else None,
        "memory": loaded_model_snapshot(endpoint, runtime_id),
    }


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(cases)
    first_wall = [float(case["first_wall_ms"]) for case in cases]
    tokens_per_second: list[float] = []
    vram_ratios: list[float] = []
    for case in cases:
        for response_key in ("first_response", "repair_response"):
            response = case.get(response_key)
            if isinstance(response, dict) and response.get("tokens_per_second") is not None:
                tokens_per_second.append(float(response["tokens_per_second"]))
        memory = case.get("memory")
        if isinstance(memory, dict) and memory.get("gpu_residency_ratio") is not None:
            vram_ratios.append(float(memory["gpu_residency_ratio"]))
    return {
        "runs": count,
        "tool_intent_pass_rate": (
            sum(bool(case.get("intent_pass")) for case in cases) / count if count else 0.0
        ),
        "tool_repair_pass_rate": (
            sum(bool(case.get("repair_pass")) for case in cases) / count if count else 0.0
        ),
        "median_wall_ms": median(first_wall),
        "median_tokens_per_second": median(tokens_per_second),
        "median_gpu_residency_ratio": median(vram_ratios),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Gemma et Ministral sur le tool-calling natif Ollama, "
            "sans promotion automatique."
        )
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--context", type=int, default=8192)
    return parser.parse_args()


def missing_model_message(alias: str, runtime_id: str) -> str:
    return f"INFO installer {alias} explicitement avec: ollama pull {runtime_id}"


def main() -> int:
    args = parse_args()
    if not 1 <= args.repetitions <= 10:
        print("KO  repetitions doit être compris entre 1 et 10")
        return 2
    if not 2048 <= args.context <= 32768:
        print("KO  context doit être compris entre 2048 et 32768")
        return 2

    catalog = load_yaml(CONFIG / "model_catalog.yaml")
    policy = load_yaml(CONFIG / "qualification_policy.yaml")
    gate = policy.get("model_selection_challenger", {})
    if not isinstance(gate, dict):
        print("KO  contrat model_selection_challenger absent")
        return 2

    incumbent_alias = str(gate.get("incumbent_alias") or "")
    challenger_alias = str(gate.get("challenger_alias") or "")
    models = catalog.get("models", {})
    challengers = catalog.get("benchmark_challengers", {})
    if not isinstance(models, dict) or not isinstance(challengers, dict):
        print("KO  catalogue modèle invalide")
        return 2
    incumbent = models.get(incumbent_alias)
    challenger = challengers.get(challenger_alias)
    if not isinstance(incumbent, dict) or not isinstance(challenger, dict):
        print("KO  incumbent/challenger absent du catalogue")
        return 2

    pairs = [
        (incumbent_alias, str(incumbent.get("runtime_id") or "")),
        (challenger_alias, str(challenger.get("runtime_id") or "")),
    ]
    try:
        tags = request_json(f"{args.endpoint}/api/tags")
        version = request_json(f"{args.endpoint}/api/version")
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"KO  Ollama inaccessible: {exc}")
        return 2

    available = {
        str(item.get("name") or item.get("model"))
        for item in tags.get("models", [])
        if isinstance(item, dict) and (item.get("name") or item.get("model"))
    }
    missing = [
        (alias, runtime_id)
        for alias, runtime_id in pairs
        if not runtime_id or not model_available(runtime_id, available)
    ]
    if missing:
        print(
            "KO  modèles absents dans Ollama: "
            + ", ".join(f"{alias} ({runtime_id})" for alias, runtime_id in missing)
        )
        for alias, runtime_id in missing:
            if runtime_id:
                print(missing_model_message(alias, runtime_id))
        return 2

    started_at = datetime.now(UTC)
    evidence: dict[str, list[dict[str, Any]]] = {}
    protocol_errors: list[dict[str, str]] = []
    for alias, runtime_id in pairs:
        cases: list[dict[str, Any]] = []
        print(f"MODEL {alias} -> {runtime_id}")
        for index in range(1, args.repetitions + 1):
            try:
                case = run_iteration(
                    args.endpoint,
                    runtime_id,
                    args.context,
                    args.timeout,
                )
            except (
                OSError,
                urllib.error.URLError,
                json.JSONDecodeError,
                ValueError,
            ) as exc:
                protocol_errors.append(
                    {"alias": alias, "run": str(index), "error": str(exc)}
                )
                print(f"ERROR {alias} run={index}: {exc}")
                continue
            cases.append(case)
            print(
                f"RUN {index}/{args.repetitions} "
                f"intent={'PASS' if case['intent_pass'] else 'FAIL'} "
                f"repair={'PASS' if case['repair_pass'] else 'FAIL'} "
                f"wall={case['first_wall_ms']:.0f}ms"
            )
        evidence[alias] = cases

    summaries = {alias: summarize(cases) for alias, cases in evidence.items()}
    comparison_complete = not protocol_errors and all(
        len(evidence.get(alias, [])) == args.repetitions for alias, _ in pairs
    )
    payload = {
        "schema_version": "1.0.0",
        "protocol": "native_tool_calling_v1",
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "ollama_version": version.get("version"),
        "endpoint": args.endpoint,
        "context_tokens": args.context,
        "repetitions": args.repetitions,
        "incumbent_alias": incumbent_alias,
        "challenger_alias": challenger_alias,
        "models": {alias: runtime_id for alias, runtime_id in pairs},
        "summaries": summaries,
        "cases": evidence,
        "protocol_errors": protocol_errors,
        "protocol_error_count": len(protocol_errors),
        "comparison_complete": comparison_complete,
        "automatic_promotion": False,
        "human_decision_required": True,
        "qualification_effect": "required_selection_evidence_only",
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    result_path = RESULTS / f"tool_calling_challenger_{stamp}.json"
    result_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"RESULT={result_path}")
    for alias, summary in summaries.items():
        print(
            f"SUMMARY {alias}: intent={summary['tool_intent_pass_rate']:.3f} "
            f"repair={summary['tool_repair_pass_rate']:.3f} "
            f"wall_ms={summary['median_wall_ms']} "
            f"tok/s={summary['median_tokens_per_second']}"
        )
    print(f"PROTOCOL_ERROR_COUNT={len(protocol_errors)}")
    print("PROMOTION_ALLOWED=false")
    print("MANUAL_DECISION_REQUIRED=true")
    if not comparison_complete:
        print("VERDICT=INCOMPLETE")
        return 2
    print("VERDICT=MEASURED_FOR_MANUAL_SELECTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
