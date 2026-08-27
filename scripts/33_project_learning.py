from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from clawlocal.project_learning import record_learning, set_learning_profile
from clawlocal.project_orchestrator import project_path


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gestion pédagogique d'un projet OPENCLAW_LOCAL.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--profile", choices=["efficient", "balanced", "intensive"])
    parser.add_argument("--skill")
    parser.add_argument(
        "--status",
        choices=["OBSERVED", "PRACTICING", "VALIDATED", "ACQUIRED"],
    )
    parser.add_argument("--evidence", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--human-validated", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    if args.profile:
        path = set_learning_profile(project, args.profile)
        print(f"LEARNING_PROFILE={args.profile}")
        print(f"LEARNING_ROOT={path}")
    if args.skill or args.status:
        if not args.skill or not args.status:
            raise ValueError("--skill et --status doivent être fournis ensemble")
        record_learning(
            project,
            skill=args.skill,
            status=args.status,
            evidence=args.evidence,
            note=args.note,
            human_validated=args.human_validated,
        )
        print(f"SKILL={args.skill}")
        print(f"STATUS={args.status}")
    if not args.profile and not args.skill:
        raise ValueError("utiliser --profile ou --skill/--status")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
