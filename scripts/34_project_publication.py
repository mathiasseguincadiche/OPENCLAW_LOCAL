from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from clawlocal.project_orchestrator import project_path
from clawlocal.project_publication import (
    record_publication_evidence,
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
    parser = argparse.ArgumentParser(description="Machine d'états de publication projet.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--evidence-key")
    parser.add_argument("--evidence-value")
    parser.add_argument("--target")
    parser.add_argument("--actor", default="human")
    parser.add_argument("--human-approved", action="store_true")
    return parser.parse_args()


def _coerce(value: str) -> bool | str:
    lowered = value.strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    return value


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    payload = None
    if args.evidence_key:
        if args.evidence_value is None:
            raise ValueError("--evidence-key exige --evidence-value")
        payload = record_publication_evidence(
            project,
            args.evidence_key,
            _coerce(args.evidence_value),
            actor=args.actor,
        )
    if args.target:
        payload = transition_publication(
            project,
            args.target,
            actor=args.actor,
            human_approved=args.human_approved,
        )
    if payload is None:
        path = project / "context" / "publication.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, PermissionError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
