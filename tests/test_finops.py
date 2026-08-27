import json
from datetime import UTC, datetime
from pathlib import Path

from clawlocal.finops import current_spend_eur


def test_current_spend_separates_daily_and_monthly(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    rows = [
        {"timestamp": "2026-08-27T10:00:00+00:00", "cost_eur": 0.4},
        {"timestamp": "2026-08-26T10:00:00+00:00", "cost_eur": 0.6},
        {"timestamp": "2026-07-27T10:00:00+00:00", "cost_eur": 9.0},
    ]
    ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    spend = current_spend_eur(ledger, now=datetime(2026, 8, 27, 12, 0, tzinfo=UTC))
    assert spend == {"daily": 0.4, "monthly": 1.0}
