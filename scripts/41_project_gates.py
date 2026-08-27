from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_governance import (
    criticality_gate_status,
    record_criticality_gate,
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
        description="Enregistre et vérifie les gates de criticité d'un projet."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--action", choices=["status", "record"], required=True)
    parser.add_argument("--target")
    parser.add_argument("--gate")
    parser.add_argument("--actor", default="human")
    parser.add_argument("--evidence")
    parser.add_argument("--human-approved", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    ensure_current_project_schema(project)
    if args.action == "record":
        if not args.gate or not args.evidence:
            raise ValueError("record exige --gate et --evidence")
        record_criticality_gate(
            project,
            args.gate,
            actor=args.actor,
            evidence=args.evidence,
            human_approved=args.human_approved,
        )
    print(
        json.dumps(
            criticality_gate_status(project, target=args.target),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
