from __future__ import annotations

import argparse

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
