from __future__ import annotations

import argparse
from pathlib import Path

from clawlocal.finops import (
    append_cloud_cost,
    default_ledger_path,
    settle_cloud_reservation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enregistre un coût cloud réellement observé."
    )
    parser.add_argument("--role", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--cost-eur", required=True, type=float)
    parser.add_argument("--project-id")
    parser.add_argument("--reservation-id")
    parser.add_argument("--ledger", type=Path, default=default_ledger_path())
    args = parser.parse_args()

    if args.reservation_id:
        path = settle_cloud_reservation(
            args.reservation_id,
            ledger_path=args.ledger,
            cost_eur=args.cost_eur,
        )
    else:
        path = append_cloud_cost(
            args.ledger,
            role=args.role,
            model=args.model,
            reason=args.reason,
            cost_eur=args.cost_eur,
            project_id=args.project_id,
        )
    print(f"LEDGER={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
