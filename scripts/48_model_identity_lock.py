from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def default_root() -> Path:
    value = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if value:
        return Path(value)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def _activate_repository_runtime(platform_root: Path) -> None:
    if os.name == "nt":
        managed = platform_root / "runtime" / "venv" / "Scripts" / "python.exe"
        if managed.is_file() and Path(sys.executable).resolve() != managed.resolve():
            os.execv(
                str(managed),
                [str(managed), str(Path(__file__).resolve()), *sys.argv[1:]],
            )

    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verrouille l'identité exacte des modèles qualifiés."
    )
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--action", choices=["capture", "promote", "check"], required=True)
    parser.add_argument("--allow-unqualified", action="store_true")
    args = parser.parse_args()

    _activate_repository_runtime(args.root)
    from clawlocal.model_identity import (
        capture_candidate,
        check_qualified,
        promote_candidate,
    )

    if args.action == "capture":
        path = capture_candidate(args.root)
        print(
            json.dumps(
                {"status": "CANDIDATE_CAPTURED", "path": str(path)},
                ensure_ascii=False,
            )
        )
        return 0
    if args.action == "promote":
        path = promote_candidate(args.root)
        print(
            json.dumps(
                {"status": "QUALIFIED", "path": str(path)},
                ensure_ascii=False,
            )
        )
        return 0

    status = check_qualified(args.root, allow_unqualified=args.allow_unqualified)
    print(json.dumps({"status": status}, ensure_ascii=False))
    if status in {"QUALIFIED", "UNQUALIFIED"}:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
