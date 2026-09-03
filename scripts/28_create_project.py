from __future__ import annotations

import argparse
import os
from pathlib import Path

from clawlocal.project_ingestion import ingest_project_documents
from clawlocal.project_ingestion_pre_v1 import ensure_secure_generic_zip_ingestion
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
    ingestion_index = ingest_project_documents(project)
    ingestion_index = ensure_secure_generic_zip_ingestion(project)
    print(f"PROJECT={project}")
    print(f"INGESTION_INDEX={ingestion_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
