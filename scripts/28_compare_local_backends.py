from __future__ import annotations

import argparse
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
DEFAULT_OLLAMA = "http://127.0.0.1:11434"
DEFAULT_SYCL = "http://127.0.0.1:8080/v1"

SCENARIOS = (
    {
        "id": "structured-devops",
        "prompt": (
            "Réponds en JSON compact avec exactement les clés diagnostic, action, rollback. "
            "Incident: un Deployment Kubernetes reste à 0/2 Ready après changement d'image. "
            "N'invente pas la cause; donne une vérification concrète."
        ),
        "max_tokens": 128,
    },
    {
        "id": "tool-intent",
        "prompt": (
            "Réponds en JSON compact avec exactement les clés tool, target, reason. "
            "Tu dois inspecter les logs du service api dans le namespace prod "
            "sans modifier le cluster."
        ),
        "max_tokens": 96,
    },
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML invalide: {path}")
    return data


def required_models() -> list[str]:
    catalog = load_yaml(CONFIG / "model_catalog.yaml")
    models = [
        str(model["runtime_id"])
        for model in catalog["models"].values()
        if model.get("required") is True
    ]
    if len(models) != 3:
        raise ValueError(
            f"La comparaison exige exactement 3 modèles required, reçus: {models}"
        )
    return models


def post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"Réponse JSON inattendue depuis {url}")
    return value


def get_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"Réponse JSON inattendue depuis {url}")
    return value


def _sycl_router_base(endpoint: str) -> str:
    normalized = endpoint.rstrip("/")
    return normalized[:-3] if normalized.endswith("/v1") else normalized


def unload_sycl_model(
    endpoint: str,
    model: str,
    *,
    timeout: float = 90.0,
) -> None:
    router = _sycl_router_base(endpoint)
    response = post_json(
        f"{router}/models/unload",
        {"model": model},
        min(timeout, 30.0),
    )
    if response.get("success") is False:
        raise RuntimeError(f"Le routeur Intel SYCL a refusé l'unload de {model}")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        inventory = get_json(f"{router}/models?reload=1", timeout=10)
        matches = [
            item
            for item in inventory.get("data", [])
            if str(item.get("id", "")).casefold() == model.casefold()
        ]
        if not matches:
            return
        status = str((matches[0].get("status") or {}).get("value") or "")
        if status == "unloaded":
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"Le modèle Intel SYCL {model} n'est pas unloaded après {timeout:.0f}s"
    )


def _rate(count: object, duration_ns: object) -> float | None:
    count_value = int(count or 0)
    duration_value = int(duration_ns or 0)
    if count_value <= 0 or duration_value <= 0:
        return None
    return count_value / duration_value * 1_000_000_000


def run_ollama(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "keep_alive": "15m",
        "think": False,
        "options": {
            "temperature": 0,
            "num_ctx": 8192,
            "num_predict": max_tokens,
        },
    }
    started = time.perf_counter()
    response = post_json(f"{endpoint}/api/chat", payload, timeout)
    wall_ms = (time.perf_counter() - started) * 1000
    message = response.get("message") or {}
    content = str(message.get("content") or "").strip()
    thinking = str(message.get("thinking") or "").strip()
    return {
        "content": content,
        "thinking_present": bool(thinking),
        "wall_ms": wall_ms,
        "load_ms": float(response.get("load_duration") or 0) / 1_000_000,
        "prompt_tokens": int(response.get("prompt_eval_count") or 0),
        "output_tokens": int(response.get("eval_count") or 0),
        "prompt_tokens_per_second": _rate(
            response.get("prompt_eval_count"), response.get("prompt_eval_duration")
        ),
        "tokens_per_second": _rate(
            response.get("eval_count"), response.get("eval_duration")
        ),
        "finish_reason": str(response.get("done_reason") or ""),
    }


def run_sycl(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        started = time.perf_counter()
        response = post_json(f"{endpoint}/chat/completions", payload, timeout)
        wall_ms = (time.perf_counter() - started) * 1000
        choices = response.get("choices") or []
        if not choices:
            raise ValueError(f"llama.cpp n'a retourné aucun choix pour {model}")
        choice = choices[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "").strip()
        reasoning_content = str(message.get("reasoning_content") or "").strip()
        timings = response.get("timings") or {}
        usage = response.get("usage") or {}
        result = {
            "content": content,
            "reasoning_content_present": bool(reasoning_content),
            "wall_ms": wall_ms,
            "load_ms": None,
            "prompt_tokens": int(
                usage.get("prompt_tokens") or timings.get("prompt_n") or 0
            ),
            "output_tokens": int(
                usage.get("completion_tokens") or timings.get("predicted_n") or 0
            ),
            "prompt_tokens_per_second": _optional_float(
                timings.get("prompt_per_second")
            ),
            "tokens_per_second": _optional_float(timings.get("predicted_per_second")),
            "finish_reason": str(choice.get("finish_reason") or ""),
            "unloaded_after_case": True,
        }
    except Exception:
        try:
            unload_sycl_model(endpoint, model)
        except Exception:
            pass
        raise
    unload_sycl_model(endpoint, model)
    return result


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def median_metric(cases: list[dict[str, Any]], key: str) -> float | None:
    values = [float(case[key]) for case in cases if case.get(key) is not None]
    return statistics.median(values) if values else None


def summarize(cases: list[dict[str, Any]], models: list[str]) -> dict[str, Any]:
    by_model: dict[str, Any] = {}
    for model in models:
        model_summary: dict[str, Any] = {}
        for backend in ("ollama-vulkan", "llama-cpp-sycl"):
            selected = [
                case
                for case in cases
                if case["model"] == model
                and case["backend"] == backend
                and case["status"] == "ok"
            ]
            model_summary[backend] = {
                "successful_cases": len(selected),
                "median_wall_ms": median_metric(selected, "wall_ms"),
                "median_tokens_per_second": median_metric(
                    selected, "tokens_per_second"
                ),
                "median_prompt_tokens_per_second": median_metric(
                    selected, "prompt_tokens_per_second"
                ),
            }
        ollama_tps = model_summary["ollama-vulkan"]["median_tokens_per_second"]
        sycl_tps = model_summary["llama-cpp-sycl"]["median_tokens_per_second"]
        speedup = (
            float(sycl_tps) / float(ollama_tps)
            if ollama_tps and sycl_tps
            else None
        )
        model_summary["sycl_decode_speedup_vs_ollama"] = speedup
        by_model[model] = model_summary

    errors = [case for case in cases if case["status"] != "ok"]
    complete = not errors and all(
        by_model[model][backend]["successful_cases"] > 0
        for model in models
        for backend in ("ollama-vulkan", "llama-cpp-sycl")
    )
    return {
        "complete": complete,
        "errors": len(errors),
        "models": by_model,
        "promotion_allowed": False,
        "note": (
            "Cette preuve compare les performances mais ne remplace pas les gates "
            "OpenClaw E2E, tool-calling, stabilité et revue humaine."
        ),
    }


def _resolve_sycl_models(advertised: set[str], models: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for model in models:
        matches = [
            candidate
            for candidate in advertised
            if candidate.casefold() == model.casefold()
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Modèle Intel SYCL non résolu: {model}; annoncés: {sorted(advertised)}"
            )
        resolved[model] = matches[0]
    return resolved


def _check_endpoints(ollama: str, sycl: str, models: list[str]) -> dict[str, str]:
    tags = get_json(f"{ollama}/api/tags")
    ollama_models = {
        str(item.get("name") or item.get("model")) for item in tags.get("models", [])
    }
    missing_ollama = [model for model in models if model not in ollama_models]
    if missing_ollama:
        raise RuntimeError(f"Modèles Ollama absents: {missing_ollama}")

    inventory = get_json(f"{sycl}/models?reload=1", timeout=10)
    sycl_models = {str(item.get("id")) for item in inventory.get("data", [])}
    return _resolve_sycl_models(sycl_models, models)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare les mêmes modèles sur Ollama/Vulkan et llama.cpp/SYCL."
    )
    parser.add_argument("--ollama", default=DEFAULT_OLLAMA)
    parser.add_argument("--sycl", default=DEFAULT_SYCL)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repetitions < 1 or args.repetitions > 5:
        raise ValueError("--repetitions doit être compris entre 1 et 5")

    models = required_models()
    scenarios = SCENARIOS[:1] if args.quick else SCENARIOS
    sycl_model_ids = _check_endpoints(args.ollama, args.sycl, models)

    cases: list[dict[str, Any]] = []
    plan_total = len(models) * len(scenarios) * args.repetitions * 2
    current = 0
    started_at = datetime.now(UTC)
    run_started = time.perf_counter()
    print(
        "BACKEND_COMPARE_PLAN "
        f"modeles={len(models)} scenarios={len(scenarios)} "
        f"repetitions={args.repetitions} requetes={plan_total}"
    )

    for model in models:
        for scenario in scenarios:
            for repetition in range(1, args.repetitions + 1):
                for backend in ("ollama-vulkan", "llama-cpp-sycl"):
                    current += 1
                    runtime_model = (
                        model if backend == "ollama-vulkan" else sycl_model_ids[model]
                    )
                    print(
                        f"[{current}/{plan_total}] {backend} model={model} "
                        f"runtime_model={runtime_model} "
                        f"scenario={scenario['id']} run={repetition}"
                    )
                    base = {
                        "backend": backend,
                        "model": model,
                        "runtime_model": runtime_model,
                        "scenario": scenario["id"],
                        "repetition": repetition,
                    }
                    try:
                        if backend == "ollama-vulkan":
                            result = run_ollama(
                                args.ollama,
                                runtime_model,
                                str(scenario["prompt"]),
                                int(scenario["max_tokens"]),
                                args.timeout,
                            )
                        else:
                            result = run_sycl(
                                args.sycl,
                                runtime_model,
                                str(scenario["prompt"]),
                                int(scenario["max_tokens"]),
                                args.timeout,
                            )
                        if not result["content"]:
                            thinking = bool(
                                result.get("thinking_present")
                                or result.get("reasoning_content_present")
                            )
                            suffix = " malgré un canal de raisonnement" if thinking else ""
                            raise ValueError(f"Réponse finale vide{suffix}")
                        case = {**base, **result, "status": "ok"}
                        cases.append(case)
                        print(
                            "    OK "
                            f"wall={result['wall_ms'] / 1000:.1f}s "
                            f"tok/s={result['tokens_per_second']} "
                            f"prompt_tok/s={result['prompt_tokens_per_second']}"
                        )
                    except (
                        OSError,
                        TimeoutError,
                        urllib.error.URLError,
                        json.JSONDecodeError,
                        ValueError,
                        RuntimeError,
                    ) as exc:
                        cases.append(
                            {
                                **base,
                                "status": "error",
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        print(f"    ERROR {type(exc).__name__}: {exc}")

    summary = summarize(cases, models)
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d_%H%M%S")
    output = RESULTS / f"backend_compare_b580_{stamp}.json"
    payload = {
        "schema_version": "1.4.0",
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "total_wall_ms": (time.perf_counter() - run_started) * 1000,
        "protocol": {
            "context_tokens": 8192,
            "temperature": 0,
            "ollama_thinking": "off_for_all_models_via_think_false",
            "sycl_thinking": "off_for_comparability_via_chat_template_kwargs",
            "sycl_explicit_unload_between_cases": True,
            "timeout_seconds": args.timeout,
            "repetitions": args.repetitions,
            "quick": args.quick,
            "scenarios": [str(item["id"]) for item in scenarios],
            "sycl_model_ids": sycl_model_ids,
        },
        "cases": cases,
        "summary": summary,
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"RESULT={output}")
    for model, report in summary["models"].items():
        speedup = report["sycl_decode_speedup_vs_ollama"]
        speedup_text = f"{speedup:.2f}x" if speedup is not None else "n/a"
        print(f"SUMMARY {model} sycl_decode_speedup_vs_ollama={speedup_text}")
    print("PROMOTION_ALLOWED=false")
    return 0 if summary["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
