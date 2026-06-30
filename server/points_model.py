"""INJ 积分 (platform credits) — per-wallet balance + append-only ledger.

Users top up by sending native INJ to the operator treasury on Injective; the
deposit scanner credits points (1 INJ = service_config.points_rate, default 100),
idempotent by on-chain tx hash. Points are spent to run agents (the engine debits
points_per_tick every decision tick). Every mutation goes through `_apply` so the
balance row and the ledger can never drift apart. (Ported from inj_ai.)
"""
from __future__ import annotations
import time
from typing import Any, Dict, List

from . import db


def balance(address: str) -> float:
    address = (address or "").lower()
    row = db.query_one("SELECT balance FROM points_ledger WHERE address=?", (address,))
    return float(row["balance"]) if row else 0.0


def _apply(address: str, delta: float, kind: str, *, token: str = "", token_amount: float = 0.0,
           txhash: str = "", note: str = "") -> float:
    address = (address or "").lower()
    now = time.time()
    with db._LOCK:   # serialize read-modify-write across threads
        cur = balance(address)
        new = cur + delta
        if new < -1e-9:
            raise ValueError("insufficient points")
        new = max(0.0, new)
        db.execute(
            "INSERT INTO points_ledger(address, balance, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(address) DO UPDATE SET balance=excluded.balance, updated_at=excluded.updated_at",
            (address, new, now),
        )
        db.execute(
            "INSERT INTO points_tx(address, kind, points, token, token_amount, txhash, note, ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (address, kind, delta, token or "", float(token_amount or 0), txhash or "", note or "", now),
        )
    return new


def credit(address: str, points: float, kind: str = "grant", **kw) -> float:
    if points <= 0:
        raise ValueError("points must be > 0")
    return _apply(address, abs(float(points)), kind, **kw)


def debit(address: str, points: float, kind: str = "spend", **kw) -> float:
    if points <= 0:
        raise ValueError("points must be > 0")
    return _apply(address, -abs(float(points)), kind, **kw)


def try_debit(address: str, points: float, kind: str = "spend", **kw) -> bool:
    """Non-raising debit used on the hot tick path. False if balance too low."""
    try:
        debit(address, points, kind, **kw)
        return True
    except ValueError:
        return False


def seen_txhash(txhash: str) -> bool:
    """True if a deposit with this on-chain tx was already credited (idempotency)."""
    if not txhash:
        return False
    return db.query_one("SELECT 1 FROM points_tx WHERE txhash=?", (txhash,)) is not None


def history(address: str, limit: int = 50) -> List[Dict[str, Any]]:
    address = (address or "").lower()
    return db.query_all(
        "SELECT kind, points, token, token_amount, txhash, note, ts FROM points_tx "
        "WHERE address=? ORDER BY id DESC LIMIT ?",
        (address, int(limit)),
    )
