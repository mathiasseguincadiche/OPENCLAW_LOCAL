from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from clawlocal.finops import (
    cloud_budget_allowed,
    default_cloud_reservation_eur,
    default_ledger_path,
)
from clawlocal.project_governance import cloud_policy_for_project
from clawlocal.project_migrations import ensure_current_project_schema
from clawlocal.project_orchestrator_superset import load_project_manifest, project_path
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
        description="Route une requête vers OpenClaw sans fallback cloud silencieux."
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Demande une escalade cloud explicite.",
    )
    parser.add_argument("--reason", help="Motif versionné dans escalation_policy.yaml.")
    parser.add_argument("--specialist-available", action="store_true")
    parser.add_argument("--deep-local-available", action="store_true")
    parser.add_argument("--local-web-attempted", action="store_true")
    parser.add_argument("--source-conflict-observed", action="store_true")
    parser.add_argument("--failure-evidence", action="store_true")
    parser.add_argument("--local-attempts", type=int, default=0)
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--project-id")
    parser.add_argument("--project-redacted", action="store_true")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--proposed-cost-eur", type=float)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    budget_ok = False
    budget_reason = "not_required"
    reservation_eur: float | None = None
    project: Path | None = None
    project_governance: dict[str, Any] | None = None

    if args.project_id:
        project = project_path(args.root, args.project_id)
        ensure_current_project_schema(project)
        manifest = load_project_manifest(project)
        if args.cloud:
            project_governance = cloud_policy_for_project(
                manifest,
                redacted=args.project_redacted,
                human_approved=args.human_approved,
            )
            if project_governance["allowed"] is not True:
                raise PermissionError(
                    "escalade cloud refusée par classification/criticité projet"
                )

    if args.cloud:
        reservation_eur = (
            args.proposed_cost_eur
            if args.proposed_cost_eur is not None
            else default_cloud_reservation_eur()
        )
        budget_ok, budget_reason = cloud_budget_allowed(
            default_ledger_path(),
            proposed_cost_eur=reservation_eur,
            project_id=args.project_id,
        )

    decision, resolved_model = route_request(
        args.agent,
        request_cloud=args.cloud,
        reason=args.reason,
        specialist_available=args.specialist_available,
        deep_local_available=args.deep_local_available,
        budget_ok=budget_ok,
        local_web_attempted=args.local_web_attempted,
        source_conflict_observed=args.source_conflict_observed,
        failure_evidence=args.failure_evidence,
        local_attempts=args.local_attempts,
        human_approved=args.human_approved,
    )
    evidence: dict[str, Any] = route_evidence(decision, resolved_model)
    evidence["project_id"] = args.project_id
    evidence["project_governance"] = project_governance
    evidence["budget"] = {
        "allowed": budget_ok if args.cloud else None,
        "reason": budget_reason,
        "reservation_eur": reservation_eur,
    }
    command = build_openclaw_agent_command(decision, resolved_model, args.message)
    evidence["command"] = command[:-3] + ["<message>", "--json"]

    if not args.execute:
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    if decision.route_kind == "cloud_escalation" and not os.environ.get(
        "OPENROUTER_API_KEY"
    ):
        raise RuntimeError("OPENROUTER_API_KEY absent: escalade cloud refusée.")

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
