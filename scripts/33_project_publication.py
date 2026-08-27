from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_orchestrator import project_path
from clawlocal.project_publication import (
    load_publication,
    set_publication_evidence,
    transition_publication,
)


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gouvernance de publication d'un projet OPENCLAW_LOCAL."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument(
        "--action",
        required=True,
        choices=["status", "evidence", "transition"],
    )
    parser.add_argument("--key")
    parser.add_argument("--value")
    parser.add_argument("--target")
    parser.add_argument("--reason", default="publication lifecycle")
    parser.add_argument("--actor", default="human")
    parser.add_argument("--human-approved", action="store_true")
    return parser.parse_args()


def _parse_value(value: str | None) -> bool | str:
    if value is None:
        raise ValueError("--value est requis")
    lowered = value.strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    return value


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    if args.action == "status":
        payload = load_publication(project)
    elif args.action == "evidence":
        if not args.key:
            raise ValueError("--key est requis pour evidence")
        payload = set_publication_evidence(
            project,
            key=args.key,
            value=_parse_value(args.value),
        )
    else:
        if not args.target:
            raise ValueError("--target est requis pour transition")
        payload = transition_publication(
            project,
            args.target,
            actor=args.actor,
            reason=args.reason,
            human_approved=args.human_approved,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
