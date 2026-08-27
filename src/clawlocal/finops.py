from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract


def platform_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def default_cloud_reservation_eur() -> float:
    policy = load_contract("budget_policy.yaml")
    return float(policy["behavior"]["default_reservation_eur"])


def default_ledger_path() -> Path:
    relative = Path(load_contract("budget_policy.yaml")["ledger"]["relative_path"])
    return platform_root() / relative


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("ligne FinOps invalide")
        rows.append(value)
    return rows


def _row_timestamp(row: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))


def current_spend_eur(path: Path, *, now: datetime | None = None) -> dict[str, float]:
    moment = now or datetime.now(UTC)
    daily = 0.0
    monthly = 0.0
    for row in _read_ledger(path):
        timestamp = _row_timestamp(row)
        cost = float(row.get("cost_eur") or 0.0)
        if (timestamp.year, timestamp.month) == (moment.year, moment.month):
            monthly += cost
            if timestamp.date() == moment.date():
                daily += cost
    return {"daily": round(daily, 6), "monthly": round(monthly, 6)}


def project_spend_eur(path: Path, project_id: str, *, now: datetime | None = None) -> float:
    moment = now or datetime.now(UTC)
    total = 0.0
    for row in _read_ledger(path):
        if row.get("project_id") != project_id:
            continue
        timestamp = _row_timestamp(row)
        if (timestamp.year, timestamp.month) == (moment.year, moment.month):
            total += float(row.get("cost_eur") or 0.0)
    return round(total, 6)


def cloud_budget_allowed(ledger_path: Path | None = None, *, proposed_cost_eur: float = 0.0, project_id: str | None = None, now: datetime | None = None) -> tuple[bool, str]:
    if proposed_cost_eur < 0:
        raise ValueError("proposed_cost_eur doit être positif")
    policy = load_contract("budget_policy.yaml")
    path = ledger_path or default_ledger_path()
    spend = current_spend_eur(path, now=now)
    daily_limit = float(policy["limits"]["daily_eur"])
    monthly_limit = float(policy["limits"]["monthly_eur"])
    projected_daily = spend["daily"] + proposed_cost_eur
    projected_monthly = spend["monthly"] + proposed_cost_eur
    if projected_daily > daily_limit:
        return False, f"daily_budget_exceeded:{projected_daily:.4f}>{daily_limit:.4f}"
    if projected_monthly > monthly_limit:
        return False, f"monthly_budget_exceeded:{projected_monthly:.4f}>{monthly_limit:.4f}"
    if project_id:
        project_limit = float(policy["limits"]["per_project_eur"])
        projected_project = project_spend_eur(path, project_id, now=now) + proposed_cost_eur
        if projected_project > project_limit:
            return False, f"project_budget_exceeded:{projected_project:.4f}>{project_limit:.4f}"
    return True, "budget_ok"


def append_cloud_cost(ledger_path: Path | None = None, *, role: str, model: str, reason: str, cost_eur: float, project_id: str | None = None) -> Path:
    if cost_eur < 0:
        raise ValueError("cost_eur doit être positif")
    path = ledger_path or default_ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": datetime.now(UTC).isoformat(), "role": role, "model": model, "reason": reason, "project_id": project_id, "cost_eur": round(float(cost_eur), 8)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path
