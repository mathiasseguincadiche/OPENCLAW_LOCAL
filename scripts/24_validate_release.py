from __future__ import annotations

import argparse
from pathlib import Path

from clawlocal.release_readiness import (
    requires_v1_readiness,
    validate_v1_release_readiness,
)
from clawlocal.versioning import validate_release_tag

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Valide SemVer puis exige l'attestation de qualification matérielle "
            "pour toute release >=1.0.0."
        )
    )
    parser.add_argument("--tag")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        version = validate_release_tag(ROOT, args.tag)
        validate_v1_release_readiness(ROOT, version)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"KO  release: {exc}")
        return 2

    print(f"OK  release SemVer cohérente: {version}")
    if requires_v1_readiness(version):
        print("OK  V1 Release Readiness: preuves hashées + approbation humaine présentes")
    else:
        print("INFO V1 Release Readiness non applicable aux versions 0.x de développement")
    if args.tag:
        print(f"OK  tag: {args.tag}")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
