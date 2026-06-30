"""Operator view of the INJ credit economy (extracted from Maneki Inj).

Read-only aggregates for an operator dashboard: per-wallet balance, total credits
spent (sum of negative ledger deltas = agent runtime burned), and total INJ
deposited. Personal data is just the wallet address — no keys, no PII.
"""
from __future__ import annotations
from typing import Any, Dict, List

from . import db, points_model


def list_user_credits() -> List[Dict[str, Any]]:
    bal = {r["address"]: float(r["balance"]) for r in
           db.query_all("SELECT address, balance FROM points_ledger")}
    spent = {r["address"]: float(r["s"] or 0) for r in
             db.query_all("SELECT address, -SUM(points) s FROM points_tx WHERE points < 0 GROUP BY address")}
    deposited = {r["address"]: float(r["d"] or 0) for r in
                 db.query_all("SELECT address, SUM(token_amount) d FROM points_tx WHERE kind='deposit' GROUP BY address")}
    addrs = set(bal) | set(spent) | set(deposited)
    rows = [{
        "address": a,
        "balance": round(bal.get(a, 0.0), 2),
        "spent": round(spent.get(a, 0.0), 2),       # credits burned by agents
        "inj_deposited": round(deposited.get(a, 0.0), 6),
    } for a in addrs]
    return sorted(rows, key=lambda x: -x["balance"])


def user_credits(address: str) -> Dict[str, Any]:
    address = (address or "").lower()
    return {
        "address": address,
        "balance": points_model.balance(address),
        "history": points_model.history(address, 100),
    }
