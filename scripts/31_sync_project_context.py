from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_context import AGENT_IDS, sync_project_context, sync_project_to_all_agents


def default_root() -> Path:
    return Path(os.environ.get("OPENCLAW_LOCAL_ROOT", "E:/AI/OpenClawLocal"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronise un Project Intake vers les workspaces.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--agent", choices=[*AGENT_IDS, "all"], default="all")
    parser.add_argument("--root", type=Path, default=default_root())
    args = parser.parse_args()
    targets = (
        sync_project_to_all_agents(args.root, args.project)
        if args.agent == "all"
        else [sync_project_context(args.root, args.project, args.agent)]
    )
    for target in targets:
        print(f"SYNCED={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
