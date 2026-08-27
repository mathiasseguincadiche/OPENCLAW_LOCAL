import json
from datetime import UTC, datetime
from pathlib import Path

from clawlocal.finops import cloud_budget_allowed, current_spend_eur, project_spend_eur


def test_current_spend_separates_daily_and_monthly(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    rows = [
        {"timestamp": "2026-08-27T10:00:00+00:00", "cost_eur": 0.4, "project_id": "p1"},
        {"timestamp": "2026-08-26T10:00:00+00:00", "cost_eur": 0.6, "project_id": "p1"},
        {"timestamp": "2026-07-27T10:00:00+00:00", "cost_eur": 9.0, "project_id": "p1"},
    ]
    ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    now = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    assert current_spend_eur(ledger, now=now) == {"daily": 0.4, "monthly": 1.0}
    assert project_spend_eur(ledger, "p1", now=now) == 1.0


def test_budget_enforces_per_project_limit(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    row = {"timestamp": "2026-08-27T10:00:00+00:00", "cost_eur": 1.9, "project_id": "p1"}
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    allowed, reason = cloud_budget_allowed(ledger, proposed_cost_eur=0.2, project_id="p1", now=datetime(2026, 8, 27, 12, 0, tzinfo=UTC))
    assert allowed is False
    assert reason.startswith("project_budget_exceeded")
