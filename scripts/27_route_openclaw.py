from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from clawlocal.project_migrations import ensure_current_project_schema
from clawlocal.project_orchestrator_superset import project_path
from clawlocal.runtime import build_openclaw_agent_command, route_evidence, route_request
from clawlocal.telemetry import automatic_run_telemetry, extract_observed_metrics


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Route une requête OpenClaw exclusivement vers la flotte locale V2."
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument(
        "--cloud",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--specialist-available",
        action="store_true",
        help="Force le tier spécialiste local pour un test/diagnostic explicite.",
    )
    parser.add_argument(
        "--deep-local-available",
        action="store_true",
        help="Force le tier deep local pour un test/diagnostic explicite.",
    )
    parser.add_argument(
        "--max-local-available",
        action="store_true",
        help="Force le tier max local pour un test/diagnostic explicite.",
    )
    parser.add_argument(
        "--producer-model-alias",
        help="Alias du modèle producteur pour renforcer l'indépendance de l'auditeur.",
    )
    parser.add_argument("--project-id")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cloud:
        raise PermissionError(
            "Architecture V2 local-only: l'option cloud n'est plus supportée"
        )

    project: Path | None = None
    if args.project_id:
        project = project_path(args.root, args.project_id)
        ensure_current_project_schema(project)

    decision, resolved_model = route_request(
        args.agent,
        specialist_available=args.specialist_available,
        deep_local_available=args.deep_local_available,
        max_local_available=args.max_local_available,
        producer_model_alias=args.producer_model_alias,
    )
    evidence: dict[str, Any] = route_evidence(decision, resolved_model)
    evidence["project_id"] = args.project_id
    command = build_openclaw_agent_command(decision, resolved_model, args.message)
    evidence["command"] = command[:-3] + ["<message>", "--json"]

    if not args.execute:
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0

    observed: dict[str, Any]
    telemetry_context = (
        automatic_run_telemetry(
            project,
            project_id=args.project_id or "unscoped",
            agent=args.agent,
            model=resolved_model,
            backend=resolved_model.split("/", maxsplit=1)[0],
            route_kind=decision.route_kind,
            phase="route",
        )
        if project is not None
        else None
    )
    if telemetry_context is None:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
        observed = {}
    else:
        with telemetry_context as observed:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
            if completed.stdout:
                try:
                    parsed = json.loads(completed.stdout)
                    observed.update(extract_observed_metrics(parsed))
                except json.JSONDecodeError:
                    pass

    evidence["returncode"] = completed.returncode
    if completed.stdout:
        try:
            evidence["openclaw"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            evidence["stdout"] = completed.stdout
    if completed.stderr:
        evidence["stderr"] = completed.stderr
    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, PermissionError, ValueError, RuntimeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
