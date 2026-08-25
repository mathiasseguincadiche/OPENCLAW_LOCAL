from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from clawlocal.qualification import evaluate_benchmark

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks" / "results"
POLICY = ROOT / "config" / "v1" / "qualification_policy.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Évalue une preuve de benchmark sans promouvoir de modèle."
    )
    parser.add_argument("path", nargs="?", type=Path)
    return parser.parse_args()


def latest_benchmark() -> Path:
    candidates = sorted(RESULTS.glob("benchmark_*.json"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError("aucun benchmark trouvé dans benchmarks/results")
    return candidates[-1]


def main() -> int:
    args = parse_args()
    path = args.path or latest_benchmark()
    payload = json.loads(path.read_text(encoding="utf-8"))
    with POLICY.open(encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    report = evaluate_benchmark(payload, policy)
    output = path.with_suffix(".evaluation.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for alias, model in report["models"].items():
        print(
            f"{alias}: gate={model['automated_gate']} pass={model['check_pass_rate']:.3f} "
            f"tps={model['median_tokens_per_second']} p95_ttft_ms={model['p95_ttft_ms']}"
        )
        for failure in model["failures"]:
            print(f"  KO  {failure}")
    print(f"VERDICT={report['verdict']}")
    print(f"EVALUATION={output}")
    return 0 if report["automated_gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
