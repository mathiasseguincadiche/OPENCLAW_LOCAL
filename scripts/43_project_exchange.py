from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_artifact_exchange import (
    validate_exchange_completeness,
    validate_exchange_for_task,
)
from clawlocal.project_intake import validate_project_id


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audite les bundles d'échange entre tâches et agents."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--task")
    parser.add_argument("--root", type=Path, default=default_root())
    args = parser.parse_args()

    project_id = validate_project_id(args.project)
    project = args.root / "projects" / project_id
    if not (project / "project.json").is_file():
        raise FileNotFoundError(project / "project.json")

    failures = (
        validate_exchange_for_task(project, args.task)
        if args.task
        else validate_exchange_completeness(project)
    )
    payload = {
        "project_id": project_id,
        "task_id": args.task,
        "status": "VALID" if not failures else "INVALID",
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
