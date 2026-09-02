from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# Always import clawlocal from the current repository checkout. The managed venv
# intentionally survives Git updates, so its site-packages copy can otherwise
# lag behind main and make configuration rendering use stale code. Reposition
# src even when an editable install already placed it later in sys.path.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SRC_ROOT_TEXT = str(SRC_ROOT)
sys.path[:] = [entry for entry in sys.path if entry != SRC_ROOT_TEXT]
sys.path.insert(0, SRC_ROOT_TEXT)

openclaw_config = importlib.import_module("clawlocal.openclaw_config")
SUPPORTED_BACKENDS = openclaw_config.SUPPORTED_BACKENDS
build_openclaw_patch = openclaw_config.build_openclaw_patch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Génère le patch OpenClaw local-first versionné."
    )
    parser.add_argument("--platform-root", required=True, type=Path)
    parser.add_argument(
        "--backend",
        choices=SUPPORTED_BACKENDS,
        default="ollama-vulkan",
        help=(
            "Backend texte local explicite; le multimodal reste sur Ollama "
            "tant que SYCL n'est pas qualifié."
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    patch = build_openclaw_patch(args.platform_root.resolve(), backend_id=args.backend)
    payload = json.dumps(patch, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
