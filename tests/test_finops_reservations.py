from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from clawlocal.finops import (
    append_cloud_cost,
    cloud_budget_allowed,
    current_spend_eur,
    reserve_cloud_budget,
    settle_cloud_reservation,
)


def test_active_reservation_blocks_concurrent_overspend(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    now = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)

    allowed, reason, reservation_id = reserve_cloud_budget(
        ledger,
        role="expert-recherche",
        model="research",
        reason="deep_web_research",
        reserved_eur=0.8,
        project_id="p1",
        now=now,
    )
    assert allowed is True
    assert reason == "budget_reserved"
    assert reservation_id

    allowed, reason, second = reserve_cloud_budget(
        ledger,
        role="ingenieur-devops",
        model="frontier-reasoning",
        reason="local_failure",
        reserved_eur=0.3,
        project_id="p2",
        now=now,
    )
    assert allowed is False
    assert reason.startswith("daily_budget_exceeded")
    assert second is None


def test_settlement_replaces_reservation_with_observed_cost(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    now = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    allowed, _, reservation_id = reserve_cloud_budget(
        ledger,
        role="expert-recherche",
        model="research",
        reason="deep_web_research",
        reserved_eur=0.8,
        project_id="p1",
        now=now,
    )
    assert allowed and reservation_id

    settle_cloud_reservation(
        reservation_id,
        ledger_path=ledger,
        cost_eur=0.55,
        now=now,
    )

    assert current_spend_eur(ledger, now=now) == {"daily": 0.55, "monthly": 0.55}
    allowed, reason = cloud_budget_allowed(
        ledger,
        proposed_cost_eur=0.45,
        now=now,
    )
    assert allowed is True
    assert reason == "budget_ok"


def test_direct_cost_append_is_atomic_with_active_reservations(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    now = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    allowed, _, reservation_id = reserve_cloud_budget(
        ledger,
        role="expert-recherche",
        model="research",
        reason="deep_web_research",
        reserved_eur=0.8,
        now=now,
    )
    assert allowed and reservation_id

    with pytest.raises(RuntimeError, match="daily_budget_exceeded"):
        append_cloud_cost(
            ledger,
            role="ingenieur-devops",
            model="frontier-reasoning",
            reason="local_failure",
            cost_eur=0.3,
            now=now,
        )


def test_expired_reservation_does_not_block_budget(tmp_path: Path) -> None:
    ledger = tmp_path / "costs.jsonl"
    initial = datetime(2026, 8, 27, 10, 0, tzinfo=UTC)
    allowed, _, reservation_id = reserve_cloud_budget(
        ledger,
        role="expert-recherche",
        model="research",
        reason="deep_web_research",
        reserved_eur=0.8,
        ttl_seconds=60,
        now=initial,
    )
    assert allowed and reservation_id

    allowed, reason = cloud_budget_allowed(
        ledger,
        proposed_cost_eur=0.8,
        now=datetime(2026, 8, 27, 12, 0, tzinfo=UTC),
    )
    assert allowed is True
    assert reason == "budget_ok"
