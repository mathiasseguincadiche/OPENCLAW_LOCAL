from __future__ import annotations

import argparse
from pathlib import Path

from clawlocal.versioning import validate_release_tag

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valide la cohérence SemVer entre VERSION, pyproject, changelog et tag."
    )
    parser.add_argument("--tag")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        version = validate_release_tag(ROOT, args.tag)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"KO  release: {exc}")
        return 2
    print(f"OK  release SemVer cohérente: {version}")
    if args.tag:
        print(f"OK  tag: {args.tag}")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
