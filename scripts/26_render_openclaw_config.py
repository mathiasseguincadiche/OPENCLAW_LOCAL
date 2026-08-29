from __future__ import annotations

import argparse
import json
from pathlib import Path

from clawlocal.openclaw_config import SUPPORTED_BACKENDS, build_openclaw_patch


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
