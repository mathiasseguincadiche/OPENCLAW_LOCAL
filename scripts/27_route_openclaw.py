from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

from clawlocal.finops import cloud_budget_allowed, default_cloud_reservation_eur, default_ledger_path
from clawlocal.runtime import build_openclaw_agent_command, route_evidence, route_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Route une requête vers OpenClaw sans fallback cloud silencieux.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--cloud", action="store_true", help="Demande une escalade cloud explicite.")
    parser.add_argument("--reason", help="Motif versionné dans escalation_policy.yaml.")
    parser.add_argument("--specialist-available", action="store_true")
    parser.add_argument("--deep-local-available", action="store_true")
    parser.add_argument("--local-web-attempted", action="store_true")
    parser.add_argument("--source-conflict-observed", action="store_true")
    parser.add_argument("--failure-evidence", action="store_true")
    parser.add_argument("--local-attempts", type=int, default=0)
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--project-id")
    parser.add_argument("--proposed-cost-eur", type=float)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    budget_ok = False
    budget_reason = "not_required"
    reservation_eur: float | None = None
    if args.cloud:
        reservation_eur = args.proposed_cost_eur if args.proposed_cost_eur is not None else default_cloud_reservation_eur()
        budget_ok, budget_reason = cloud_budget_allowed(default_ledger_path(), proposed_cost_eur=reservation_eur, project_id=args.project_id)
    decision, resolved_model = route_request(args.agent, request_cloud=args.cloud, reason=args.reason, specialist_available=args.specialist_available, deep_local_available=args.deep_local_available, budget_ok=budget_ok, local_web_attempted=args.local_web_attempted, source_conflict_observed=args.source_conflict_observed, failure_evidence=args.failure_evidence, local_attempts=args.local_attempts, human_approved=args.human_approved)
    evidence: dict[str, Any] = route_evidence(decision, resolved_model)
    evidence["project_id"] = args.project_id
    evidence["budget"] = {"allowed": budget_ok if args.cloud else None, "reason": budget_reason, "reservation_eur": reservation_eur}
    command = build_openclaw_agent_command(decision, resolved_model, args.message)
    evidence["command"] = command[:-3] + ["<message>", "--json"]
    if not args.execute:
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    if decision.route_kind == "cloud_escalation" and not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY absent: escalade cloud refusée.")
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=args.timeout)
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
    except (KeyError, PermissionError, ValueError, RuntimeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
