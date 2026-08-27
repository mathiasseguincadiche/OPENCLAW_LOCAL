from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_intake import create_project


def default_root() -> Path:
    value = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if value:
        return Path(value)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(description="Crée un Project Intake OPENCLAW_LOCAL.")
    parser.add_argument("--id", required=True, dest="project_id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--intake", action="append", default=[], type=Path)
    parser.add_argument("--source", action="append", default=[], type=Path)
    parser.add_argument("--deliverable", action="append", default=[])
    parser.add_argument("--owner", default="dirigeant-operateur")
    parser.add_argument(
        "--classification",
        choices=["public", "internal", "confidential", "restricted"],
        default="internal",
    )
    parser.add_argument(
        "--criticality",
        choices=["low", "standard", "high", "critical"],
        default="standard",
    )
    parser.add_argument("--root", type=Path, default=default_root())
    args = parser.parse_args()
    project = create_project(
        args.root,
        args.project_id,
        args.title,
        intake_items=args.intake,
        source_items=args.source,
        expected_deliverables=args.deliverable,
        owner=args.owner,
        classification=args.classification,
        criticality=args.criticality,
    )
    print(f"PROJECT={project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
