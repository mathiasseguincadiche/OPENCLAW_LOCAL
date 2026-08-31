from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _activate_repository_runtime() -> None:
    platform_root = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if platform_root and os.name == "nt":
        managed = Path(platform_root) / "runtime" / "venv" / "Scripts" / "python.exe"
        if managed.is_file() and Path(sys.executable).resolve() != managed.resolve():
            os.execv(
                str(managed),
                [str(managed), str(Path(__file__).resolve()), *sys.argv[1:]],
            )

    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


_activate_repository_runtime()

from clawlocal.config import load_contract


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Liste les modèles déclarés dans model_catalog.yaml."
    )
    parser.add_argument("--provider")
    parser.add_argument("--required", action="store_true")
    parser.add_argument("--class", dest="model_class")
    parser.add_argument(
        "--field",
        choices=("runtime_id", "alias"),
        default="runtime_id",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = load_contract("model_catalog.yaml")
    models = catalog.get("models", {})
    for alias, model in models.items():
        if args.provider and model.get("provider") != args.provider:
            continue
        if args.required and model.get("required") is not True:
            continue
        if args.model_class and model.get("class") != args.model_class:
            continue
        print(alias if args.field == "alias" else model["runtime_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
