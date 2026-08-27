from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

from clawlocal.finops import cloud_budget_allowed, default_ledger_path
from clawlocal.runtime import build_openclaw_agent_command, route_evidence, route_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Route une requête vers OpenClaw sans fallback cloud silencieux.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--cloud", action="store_true", help="Demande une escalade cloud explicite.")
    parser.add_argument("--reason", help="Motif versionné dans escalation_policy.yaml.")
    parser.add_argument("--specialist-available", action="store_true")
    parser.add_argument("--deep-local-available", action="store_true")
    parser.add_argument("--proposed-cost-eur", type=float, default=0.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    budget_ok = False
    budget_reason = "not_required"
    if args.cloud:
        budget_ok, budget_reason = cloud_budget_allowed(default_ledger_path(), proposed_cost_eur=args.proposed_cost_eur)

    decision, resolved_model = route_request(
        args.agent,
        request_cloud=args.cloud,
        reason=args.reason,
        specialist_available=args.specialist_available,
        deep_local_available=args.deep_local_available,
        budget_ok=budget_ok,
    )
    evidence: dict[str, Any] = route_evidence(decision, resolved_model)
    evidence["budget"] = {"allowed": budget_ok if args.cloud else None, "reason": budget_reason}
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
