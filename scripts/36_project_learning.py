from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_learning import (
    add_learning_objective,
    append_learning_entry,
    record_learning_evidence,
    set_learning_profile,
    set_learning_verdict,
    update_skill,
)
from clawlocal.project_migrations import ensure_current_project_schema
from clawlocal.project_orchestrator_superset import project_path


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
        choices=["profile", "journal", "skill", "objective", "evidence", "verdict"],
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
    parser.add_argument("--objective")
    parser.add_argument("--verdict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    ensure_current_project_schema(project)
    if args.action == "profile":
        if not args.profile or not args.mode:
            raise ValueError("profile exige --profile et --mode")
        print(set_learning_profile(project, profile=args.profile, mode=args.mode))
    elif args.action == "journal":
        if not args.title or not args.understanding or not args.evidence:
            raise ValueError("journal exige --title, --understanding et --evidence")
        append_learning_entry(
            project,
            title=args.title,
            understanding=args.understanding,
            evidence=args.evidence,
            next_step=args.next_step,
        )
        print(project / "context" / "learning" / "LEARNING_JOURNAL.md")
    elif args.action == "skill":
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
    elif args.action == "objective":
        if not args.objective:
            raise ValueError("objective exige --objective")
        add_learning_objective(project, objective=args.objective, skill=args.skill)
        print(project / "context" / "learning" / "LEARNING_CONTRACT.json")
    elif args.action == "evidence":
        if not args.evidence:
            raise ValueError("evidence exige --evidence")
        record_learning_evidence(project, evidence=args.evidence)
        print(project / "context" / "learning" / "LEARNING_CONTRACT.json")
    else:
        if not args.verdict:
            raise ValueError("verdict exige --verdict")
        set_learning_verdict(project, args.verdict)
        print(project / "context" / "learning" / "LEARNING_CONTRACT.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
