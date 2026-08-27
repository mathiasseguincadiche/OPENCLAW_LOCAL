from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from clawlocal.project_orchestrator import project_path
from clawlocal.telemetry import (
    append_telemetry_event,
    default_telemetry_path,
    export_project_summary,
    read_telemetry_events,
    summarize_telemetry,
)


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Télémétrie opérationnelle OPENCLAW_LOCAL.")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--project")
    parser.add_argument("--record", type=Path)
    parser.add_argument("--export-project-summary", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.record:
        payload = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("--record doit pointer vers un objet JSON")
        append_telemetry_event(args.root, payload)

    path = default_telemetry_path(args.root)
    events = read_telemetry_events(path)
    summary = summarize_telemetry(events, project_id=args.project)

    if args.export_project_summary:
        if not args.project:
            raise ValueError("--export-project-summary exige --project")
        project = project_path(args.root, args.project)
        target = export_project_summary(args.root, project)
        summary["exported_to"] = str(target)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
