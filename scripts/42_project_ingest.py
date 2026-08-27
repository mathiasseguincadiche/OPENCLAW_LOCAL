from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.project_ingestion import (
    ingest_project_documents,
    validate_ingestion_index,
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
        description="Construit ou vérifie la représentation locale des documents d'un projet."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    project_id = validate_project_id(args.project)
    project = args.root / "projects" / project_id
    if not (project / "project.json").is_file():
        raise FileNotFoundError(project / "project.json")

    index = project / "context" / "ingestion" / "index.json"
    if not args.validate_only:
        if index.exists() and not args.force:
            raise FileExistsError("ingestion déjà présente; utiliser --force pour la reconstruire")
        ingest_project_documents(project, force=args.force)
    payload = validate_ingestion_index(project)
    print(
        json.dumps(
            {
                "project_id": project_id,
                "entry_count": payload.get("entry_count", 0),
                "aggregate_sha256": payload.get("aggregate_sha256"),
                "status": "VALID",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
