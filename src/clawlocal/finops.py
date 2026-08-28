from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
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


def default_reservation_ttl_seconds() -> int:
    policy = load_contract("budget_policy.yaml")
    return int(policy["behavior"].get("reservation_ttl_seconds", 3600))


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


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def _ledger_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _row_timestamp(row: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))


def _event(row: dict[str, Any]) -> str:
    return str(row.get("event") or "cost")


def _settled_reservation_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("reservation_id"))
        for row in rows
        if _event(row) in {"settlement", "release"} and row.get("reservation_id")
    }


def _active_reservations(
    rows: list[dict[str, Any]],
    *,
    now: datetime,
    exclude_reservation_id: str | None = None,
) -> list[dict[str, Any]]:
    settled = _settled_reservation_ids(rows)
    active: list[dict[str, Any]] = []
    for row in rows:
        if _event(row) != "reservation":
            continue
        reservation_id = str(row.get("reservation_id") or "")
        if not reservation_id or reservation_id == exclude_reservation_id:
            continue
        if reservation_id in settled:
            continue
        expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        if expires_at <= now:
            continue
        active.append(row)
    return active


def _cost_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if _event(row) in {"cost", "settlement"}]


def current_spend_eur(
    path: Path,
    *,
    now: datetime | None = None,
) -> dict[str, float]:
    moment = now or datetime.now(UTC)
    daily = 0.0
    monthly = 0.0
    for row in _cost_rows(_read_ledger(path)):
        timestamp = _row_timestamp(row)
        cost = float(row.get("cost_eur") or 0.0)
        if (timestamp.year, timestamp.month) == (moment.year, moment.month):
            monthly += cost
            if timestamp.date() == moment.date():
                daily += cost
    return {
        "daily": round(daily, 6),
        "monthly": round(monthly, 6),
    }


def project_spend_eur(
    path: Path,
    project_id: str,
    *,
    now: datetime | None = None,
) -> float:
    moment = now or datetime.now(UTC)
    total = 0.0
    for row in _cost_rows(_read_ledger(path)):
        if row.get("project_id") != project_id:
            continue
        timestamp = _row_timestamp(row)
        if (timestamp.year, timestamp.month) == (moment.year, moment.month):
            total += float(row.get("cost_eur") or 0.0)
    return round(total, 6)


def _effective_spend(
    rows: list[dict[str, Any]],
    *,
    now: datetime,
    project_id: str | None = None,
    exclude_reservation_id: str | None = None,
) -> dict[str, float]:
    daily = 0.0
    monthly = 0.0
    project = 0.0
    for row in _cost_rows(rows):
        timestamp = _row_timestamp(row)
        cost = float(row.get("cost_eur") or 0.0)
        if (timestamp.year, timestamp.month) != (now.year, now.month):
            continue
        monthly += cost
        if timestamp.date() == now.date():
            daily += cost
        if project_id and row.get("project_id") == project_id:
            project += cost

    for row in _active_reservations(
        rows,
        now=now,
        exclude_reservation_id=exclude_reservation_id,
    ):
        timestamp = _row_timestamp(row)
        reserved = float(row.get("reserved_eur") or 0.0)
        if (timestamp.year, timestamp.month) != (now.year, now.month):
            continue
        monthly += reserved
        if timestamp.date() == now.date():
            daily += reserved
        if project_id and row.get("project_id") == project_id:
            project += reserved

    return {
        "daily": round(daily, 8),
        "monthly": round(monthly, 8),
        "project": round(project, 8),
    }


def _budget_allowed_rows(
    rows: list[dict[str, Any]],
    *,
    proposed_cost_eur: float,
    project_id: str | None,
    now: datetime,
    exclude_reservation_id: str | None = None,
) -> tuple[bool, str]:
    if proposed_cost_eur < 0:
        raise ValueError("proposed_cost_eur doit être positif")

    policy = load_contract("budget_policy.yaml")
    spend = _effective_spend(
        rows,
        now=now,
        project_id=project_id,
        exclude_reservation_id=exclude_reservation_id,
    )
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
        projected_project = spend["project"] + proposed_cost_eur
        if projected_project > project_limit:
            return (
                False,
                f"project_budget_exceeded:{projected_project:.4f}>{project_limit:.4f}",
            )

    return True, "budget_ok"


def cloud_budget_allowed(
    ledger_path: Path | None = None,
    *,
    proposed_cost_eur: float = 0.0,
    project_id: str | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    path = ledger_path or default_ledger_path()
    moment = now or datetime.now(UTC)
    return _budget_allowed_rows(
        _read_ledger(path),
        proposed_cost_eur=proposed_cost_eur,
        project_id=project_id,
        now=moment,
    )


def reserve_cloud_budget(
    ledger_path: Path | None = None,
    *,
    role: str,
    model: str,
    reason: str,
    reserved_eur: float,
    project_id: str | None = None,
    ttl_seconds: int | None = None,
    now: datetime | None = None,
) -> tuple[bool, str, str | None]:
    if reserved_eur < 0:
        raise ValueError("reserved_eur doit être positif")
    path = ledger_path or default_ledger_path()
    moment = now or datetime.now(UTC)
    ttl = ttl_seconds if ttl_seconds is not None else default_reservation_ttl_seconds()
    if ttl < 1:
        raise ValueError("ttl_seconds doit être >= 1")

    with _ledger_lock(path):
        rows = _read_ledger(path)
        allowed, budget_reason = _budget_allowed_rows(
            rows,
            proposed_cost_eur=reserved_eur,
            project_id=project_id,
            now=moment,
        )
        if not allowed:
            return False, budget_reason, None
        reservation_id = str(uuid.uuid4())
        _append_row(
            path,
            {
                "event": "reservation",
                "timestamp": moment.isoformat(),
                "expires_at": (moment + timedelta(seconds=ttl)).isoformat(),
                "reservation_id": reservation_id,
                "role": role,
                "model": model,
                "reason": reason,
                "project_id": project_id,
                "reserved_eur": round(float(reserved_eur), 8),
            },
        )
    return True, "budget_reserved", reservation_id


def settle_cloud_reservation(
    reservation_id: str,
    *,
    cost_eur: float,
    ledger_path: Path | None = None,
    now: datetime | None = None,
) -> Path:
    if cost_eur < 0:
        raise ValueError("cost_eur doit être positif")
    path = ledger_path or default_ledger_path()
    moment = now or datetime.now(UTC)

    with _ledger_lock(path):
        rows = _read_ledger(path)
        reservations = [
            row
            for row in rows
            if _event(row) == "reservation"
            and str(row.get("reservation_id")) == reservation_id
        ]
        if len(reservations) != 1:
            raise KeyError(f"réservation FinOps inconnue: {reservation_id}")
        if reservation_id in _settled_reservation_ids(rows):
            raise ValueError(f"réservation FinOps déjà clôturée: {reservation_id}")
        reservation = reservations[0]
        allowed, budget_reason = _budget_allowed_rows(
            rows,
            proposed_cost_eur=cost_eur,
            project_id=(
                str(reservation["project_id"])
                if reservation.get("project_id")
                else None
            ),
            now=moment,
            exclude_reservation_id=reservation_id,
        )
        if not allowed:
            raise RuntimeError(budget_reason)
        _append_row(
            path,
            {
                "event": "settlement",
                "timestamp": moment.isoformat(),
                "reservation_id": reservation_id,
                "role": reservation.get("role"),
                "model": reservation.get("model"),
                "reason": reservation.get("reason"),
                "project_id": reservation.get("project_id"),
                "cost_eur": round(float(cost_eur), 8),
            },
        )
    return path


def release_cloud_reservation(
    reservation_id: str,
    *,
    ledger_path: Path | None = None,
    now: datetime | None = None,
) -> Path:
    path = ledger_path or default_ledger_path()
    moment = now or datetime.now(UTC)
    with _ledger_lock(path):
        rows = _read_ledger(path)
        if not any(
            _event(row) == "reservation"
            and str(row.get("reservation_id")) == reservation_id
            for row in rows
        ):
            raise KeyError(f"réservation FinOps inconnue: {reservation_id}")
        if reservation_id in _settled_reservation_ids(rows):
            raise ValueError(f"réservation FinOps déjà clôturée: {reservation_id}")
        _append_row(
            path,
            {
                "event": "release",
                "timestamp": moment.isoformat(),
                "reservation_id": reservation_id,
            },
        )
    return path


def append_cloud_cost(
    ledger_path: Path | None = None,
    *,
    role: str,
    model: str,
    reason: str,
    cost_eur: float,
    project_id: str | None = None,
    now: datetime | None = None,
) -> Path:
    if cost_eur < 0:
        raise ValueError("cost_eur doit être positif")
    path = ledger_path or default_ledger_path()
    moment = now or datetime.now(UTC)

    with _ledger_lock(path):
        rows = _read_ledger(path)
        allowed, budget_reason = _budget_allowed_rows(
            rows,
            proposed_cost_eur=cost_eur,
            project_id=project_id,
            now=moment,
        )
        if not allowed:
            raise RuntimeError(budget_reason)
        _append_row(
            path,
            {
                "event": "cost",
                "timestamp": moment.isoformat(),
                "role": role,
                "model": model,
                "reason": reason,
                "project_id": project_id,
                "cost_eur": round(float(cost_eur), 8),
            },
        )
    return path
