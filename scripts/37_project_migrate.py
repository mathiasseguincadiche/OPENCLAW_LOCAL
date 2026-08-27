from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_migrations import apply_project_migrations, plan_project_migration
from clawlocal.project_orchestrator import project_path


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(description="Planifie ou applique une migration de projet.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    project = project_path(args.root, args.project)
    steps = apply_project_migrations(project) if args.apply else plan_project_migration(project)
    print(json.dumps({"project": args.project, "steps": steps}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
