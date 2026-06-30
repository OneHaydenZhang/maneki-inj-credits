"""Deposit scanner — turns on-chain INJ deposits into 积分.

Reads the operator treasury's INCOMING native-INJ MsgSend transfers and credits
the depositor with points (1 INJ = service_config.points_rate("INJ"), default 100).
Idempotent by tx hash. Attribution: the depositing address is mapped back to the
LOGIN user via `deposit_senders` (recorded when the user prepares a deposit); if
unmapped, we fall back to the sender's own address. We only ever read the
treasury's incoming transfers — its balance is never exposed.
"""
from __future__ import annotations

from . import db, points_config as service_config
from . import points_model
from . import inj_chain


def _owner_of(sender_eth: str, sender_inj: str) -> str:
    """Map a depositing wallet to the LOGIN user."""
    for key in (sender_inj or "", sender_eth or ""):
        if not key:
            continue
        row = db.query_one("SELECT address FROM deposit_senders WHERE sender_inj=?", (key.lower(),))
        if row:
            return row["address"]
    # Fall back: credit the sender's own eth address (its login, if they ever log in).
    return (sender_eth or sender_inj or "").lower()


def remember_sender(sender_inj: str, sender_eth: str, address: str) -> None:
    """Record that this depositing wallet belongs to login user `address`."""
    import time
    now = time.time()
    for key in {(sender_inj or "").lower(), (sender_eth or "").lower()}:
        if key:
            db.execute(
                "INSERT INTO deposit_senders(sender_inj, address, created_at) VALUES(?,?,?) "
                "ON CONFLICT(sender_inj) DO UPDATE SET address=excluded.address",
                (key, (address or "").lower(), now),
            )


def _belongs_to(d: dict, user: str) -> bool:
    """True iff this incoming transfer was sent BY `user` (their login address, or a
    deposit wallet they registered). We attribute by SENDER, never by balance."""
    u = (user or "").lower()
    if not u:
        return False
    if (d.get("sender_eth") or "").lower() == u:
        return True
    # explicit sender→login mapping (recorded when this user prepared a deposit)
    for key in ((d.get("sender_inj") or "").lower(), (d.get("sender_eth") or "").lower()):
        if key:
            row = db.query_one("SELECT address FROM deposit_senders WHERE sender_inj=?", (key,))
            if row and (row["address"] or "").lower() == u:
                return True
    return False


def scan_for_user(user: str) -> dict:
    """Credit ONLY the deposits that THIS user sent to the treasury.

    The correct top-up check: look at recent transfer RECORDS to the treasury and
    find ones whose SENDER is the current user's address — credit those, deduped by
    on-chain txhash. We never read the treasury BALANCE (that would hand a user a
    big batch of points on every refresh). No matching transfer → no credit.
    """
    treasury = service_config.points_treasury()
    if not treasury:
        return {"credited": 0, "credited_points": 0.0, "skipped": "no treasury"}
    network = service_config.points_treasury_network()
    rate = service_config.points_rate("INJ")
    credited = 0
    credited_points = 0.0
    try:
        deposits = inj_chain.fetch_incoming_inj(network, treasury, limit=40)
    except Exception as e:
        print(f"[inj] deposit scan failed: {e!r}")
        return {"credited": 0, "credited_points": 0.0, "error": str(e)[:120]}
    for d in deposits:
        txh = d.get("txhash")
        amt = float(d.get("amount_inj") or 0)
        if not txh or amt <= 0:
            continue
        if not _belongs_to(d, user):          # only MY transfers count
            continue
        if points_model.seen_txhash(txh):      # idempotent — refresh won't re-credit
            continue
        pts = amt * rate
        try:
            points_model.credit(user, pts, kind="deposit", token="INJ",
                                token_amount=amt, txhash=txh,
                                note=f"deposit {amt:.6f} INJ → {pts:.0f} 积分")
            credited += 1
            credited_points += pts
        except Exception as e:
            print(f"[inj] credit failed tx={txh[:12]}: {e!r}")
    return {"credited": credited, "credited_points": credited_points}


def scan_once() -> dict:
    """Background sweep: credit any not-yet-seen INJ deposit by mapped sender.
    The user-facing refresh uses scan_for_user (scoped to the caller); this exists
    only for an optional operator-side timer that backfills mapped deposits."""
    treasury = service_config.points_treasury()
    if not treasury:
        return {"credited": 0, "skipped": "no treasury"}
    network = service_config.points_treasury_network()
    rate = service_config.points_rate("INJ")
    credited = 0
    try:
        deposits = inj_chain.fetch_incoming_inj(network, treasury, limit=40)
    except Exception as e:
        print(f"[inj] deposit scan failed: {e!r}")
        return {"credited": 0, "error": str(e)[:120]}
    for d in deposits:
        txh = d.get("txhash")
        amt = float(d.get("amount_inj") or 0)
        if not txh or amt <= 0 or points_model.seen_txhash(txh):
            continue
        # background sweep ONLY credits senders we have an explicit mapping for
        # (a user who prepared a deposit). Unmapped transfers are left for the
        # owner's own scan_for_user so we never mis-attribute.
        row = None
        for key in ((d.get("sender_inj") or "").lower(), (d.get("sender_eth") or "").lower()):
            if key:
                row = db.query_one("SELECT address FROM deposit_senders WHERE sender_inj=?", (key,))
                if row:
                    break
        if not row:
            continue
        try:
            points_model.credit(row["address"], amt * rate, kind="deposit", token="INJ",
                                token_amount=amt, txhash=txh,
                                note=f"deposit {amt:.6f} INJ → {amt * rate:.0f} 积分")
            credited += 1
        except Exception as e:
            print(f"[inj] credit failed tx={txh[:12]}: {e!r}")
    return {"credited": credited}
