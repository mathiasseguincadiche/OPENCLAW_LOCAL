from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from clawlocal.model_identity import capture_candidate, check_qualified, promote_candidate


def default_root() -> Path:
    value = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if value:
        return Path(value)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verrouille l'identité exacte des modèles qualifiés.")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--action", choices=["capture", "promote", "check"], required=True)
    parser.add_argument("--allow-unqualified", action="store_true")
    args = parser.parse_args()

    if args.action == "capture":
        path = capture_candidate(args.root)
        print(json.dumps({"status": "CANDIDATE_CAPTURED", "path": str(path)}, ensure_ascii=False))
        return 0
    if args.action == "promote":
        path = promote_candidate(args.root)
        print(json.dumps({"status": "QUALIFIED", "path": str(path)}, ensure_ascii=False))
        return 0

    status = check_qualified(args.root, allow_unqualified=args.allow_unqualified)
    print(json.dumps({"status": status}, ensure_ascii=False))
    if status in {"QUALIFIED", "UNQUALIFIED"}:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
