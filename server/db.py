"""Minimal SQLite layer for the INJ credit ledger (extracted from Maneki Inj).

Holds only what the credits subsystem needs: the per-wallet balance, the
append-only ledger (with on-chain txhash for idempotency), and the
sender→login mapping used to attribute on-chain deposits.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Optional

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "credits.db"

_LOCK = threading.RLock()
_CONN: Optional[sqlite3.Connection] = None

_SCHEMA = """
-- per-wallet credit balance
CREATE TABLE IF NOT EXISTS points_ledger (
    address     TEXT PRIMARY KEY,
    balance     REAL NOT NULL DEFAULT 0,
    updated_at  REAL NOT NULL DEFAULT 0
);
-- append-only credit movements; deposits carry the on-chain txhash (dedupe key)
CREATE TABLE IF NOT EXISTS points_tx (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    address       TEXT NOT NULL,
    kind          TEXT NOT NULL DEFAULT '',     -- deposit | tick | grant | spend
    points        REAL NOT NULL DEFAULT 0,      -- signed delta
    token         TEXT NOT NULL DEFAULT '',     -- INJ
    token_amount  REAL NOT NULL DEFAULT 0,
    txhash        TEXT NOT NULL DEFAULT '',
    note          TEXT NOT NULL DEFAULT '',
    ts            REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_points_tx_addr ON points_tx(address);
CREATE INDEX IF NOT EXISTS idx_points_tx_hash ON points_tx(txhash);
-- maps a depositing inj/0x address back to the LOGIN wallet to credit
CREATE TABLE IF NOT EXISTS deposit_senders (
    sender_inj  TEXT PRIMARY KEY,
    address     TEXT NOT NULL,
    created_at  REAL NOT NULL DEFAULT 0
);
"""


def _conn() -> sqlite3.Connection:
    global _CONN
    with _LOCK:
        if _CONN is None:
            DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            c = sqlite3.connect(str(DB_FILE), check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(_SCHEMA)
            c.commit()
            _CONN = c
        return _CONN


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    with _LOCK:
        cur = _conn().execute(sql, params)
        _conn().commit()
        return cur


def query_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    with _LOCK:
        row = _conn().execute(sql, params).fetchone()
        return dict(row) if row else None


def query_all(sql: str, params: tuple = ()) -> list[Dict[str, Any]]:
    with _LOCK:
        rows = _conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]
