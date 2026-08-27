from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_context import (
    AGENT_IDS,
    sync_project_context,
    sync_project_to_all_agents,
)


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronise un Project Intake vers les workspaces."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--agent", choices=[*AGENT_IDS, "all"], default="all")
    parser.add_argument(
        "--include-outputs",
        action="store_true",
        help="Inclut travail/livrables/preuves pour un snapshot de revue.",
    )
    parser.add_argument("--root", type=Path, default=default_root())
    args = parser.parse_args()

    targets = (
        sync_project_to_all_agents(
            args.root,
            args.project,
            include_outputs=args.include_outputs,
        )
        if args.agent == "all"
        else [
            sync_project_context(
                args.root,
                args.project,
                args.agent,
                include_outputs=args.include_outputs,
            )
        ]
    )
    for target in targets:
        print(f"SYNCED={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
