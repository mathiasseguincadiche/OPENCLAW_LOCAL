from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_integrity import (
    latest_integrity_snapshot,
    snapshot_integrity,
    verify_integrity_snapshot,
)
from clawlocal.project_orchestrator import project_path


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshots SHA-256 d'intégrité projet.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--action", choices=["snapshot", "verify"], required=True)
    parser.add_argument("--phase", default="MANUAL")
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    project = project_path(args.root, args.project)
    if args.action == "snapshot":
        path = snapshot_integrity(project, args.phase)
        print(path)
        return 0
    snapshot = args.snapshot or latest_integrity_snapshot(project, args.phase)
    if snapshot is None:
        raise FileNotFoundError("aucun snapshot d'intégrité disponible")
    failures = verify_integrity_snapshot(project, snapshot)
    print(json.dumps({"snapshot": str(snapshot), "failures": failures}, indent=2))
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
