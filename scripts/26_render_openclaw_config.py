from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _activate_repository_sources() -> None:
    # Always import clawlocal from the current repository checkout. The managed
    # venv intentionally survives Git updates, so its site-packages copy can
    # otherwise lag behind main and make configuration rendering use stale code.
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    src_text = str(src)
    sys.path[:] = [entry for entry in sys.path if entry != src_text]
    sys.path.insert(0, src_text)


def _enforce_nominal_skill_prompt_budget(patch: dict[str, Any]) -> None:
    """Keep OpenClaw skill cards out of the nominal local-agent system prompt.

    OpenClaw 2026.9.x persists the authored roster canonically under
    ``agents.entries`` even when a legacy ``agents.list`` patch is accepted as an
    input surface. The no-skills allowlists remain explicit, and the global
    ``skills.limits.maxSkillsPromptChars: 0`` budget is an independent final
    backstop at prompt-render time. Future skills must be reintroduced
    deliberately per role, relax this budget explicitly, and pass the
    prompt-admission gate.
    """
    skills = patch.setdefault("skills", {})
    if not isinstance(skills, dict):
        raise ValueError("Patch OpenClaw invalide: section skills non objet")
    limits = skills.setdefault("limits", {})
    if not isinstance(limits, dict):
        raise ValueError("Patch OpenClaw invalide: skills.limits non objet")
    limits["maxSkillsPromptChars"] = 0

    agents = patch.get("agents")
    if not isinstance(agents, dict):
        raise ValueError("Patch OpenClaw invalide: section agents absente")

    defaults = agents.get("defaults")
    if not isinstance(defaults, dict):
        raise ValueError("Patch OpenClaw invalide: agents.defaults absent")
    defaults["skills"] = []

    roster = agents.get("list")
    if not isinstance(roster, list) or not roster:
        raise ValueError("Patch OpenClaw invalide: roster agents.list absent")

    for entry in roster:
        if not isinstance(entry, dict) or not str(entry.get("id", "")).strip():
            raise ValueError("Patch OpenClaw invalide: entrée agent sans id")
        entry["skills"] = []


def main() -> int:
    _activate_repository_sources()
    from clawlocal.openclaw_config import SUPPORTED_BACKENDS, build_openclaw_patch

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
    _enforce_nominal_skill_prompt_budget(patch)
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
