from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_orchestrator import project_path
from clawlocal.project_security import build_support_bundle


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crée un support bundle redigé sans Intake ni sources."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project = project_path(args.root, args.project)
    output = args.output or project / "evidence" / "support" / "support-bundle.zip"
    print(build_support_bundle(project, output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
