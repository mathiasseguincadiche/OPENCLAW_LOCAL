from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_learning import (
    append_learning_entry,
    set_learning_profile,
    update_skill,
)
from clawlocal.project_orchestrator import project_path


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Contrôle du profil pédagogique et des preuves d'apprentissage."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument(
        "--action",
        required=True,
        choices=["profile", "journal", "skill"],
    )
    parser.add_argument("--profile")
    parser.add_argument("--mode")
    parser.add_argument("--title")
    parser.add_argument("--understanding")
    parser.add_argument("--evidence")
    parser.add_argument("--next-step")
    parser.add_argument("--skill")
    parser.add_argument("--status")
    parser.add_argument("--next-review", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    if args.action == "profile":
        if not args.profile or not args.mode:
            raise ValueError("profile exige --profile et --mode")
        path = set_learning_profile(
            project,
            profile=args.profile,
            mode=args.mode,
        )
        print(path)
    elif args.action == "journal":
        if not args.title or not args.understanding or not args.evidence:
            raise ValueError(
                "journal exige --title, --understanding et --evidence"
            )
        append_learning_entry(
            project,
            title=args.title,
            understanding=args.understanding,
            evidence=args.evidence,
            next_step=args.next_step,
        )
        print(project / "context" / "learning" / "LEARNING_JOURNAL.md")
    else:
        if not args.skill or not args.status or not args.evidence:
            raise ValueError("skill exige --skill, --status et --evidence")
        update_skill(
            project,
            skill=args.skill,
            status=args.status,
            evidence=args.evidence,
            next_review=args.next_review,
        )
        print(project / "context" / "learning" / "SKILLS_MATRIX.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
