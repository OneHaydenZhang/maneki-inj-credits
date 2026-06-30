"""FastAPI routes for the INJ credit economy (extracted from Maneki Inj).

Endpoints:
  GET  /api/points                  balance + config (treasury/rate/presets) + history
  POST /api/points/deposit/build    build an unsigned INJ MsgSend for the wallet to signDirect
  POST /api/points/deposit/submit   broadcast the wallet-signed tx, then scan + credit
  POST /api/points/scan             scan recent treasury transfers SENT BY this user, credit them

NOTE: in the full Maneki Inj app the login `address` comes from a wallet-signature
session. Here it's read from an `X-Login-Address` header to keep this module
self-contained — swap `login_address` for your own auth dependency.
"""
from __future__ import annotations
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from . import points_config as cfg, points_model, deposits, inj_chain

api = APIRouter(prefix="/api")


def login_address(x_login_address: str = Header(default="")) -> str:
    addr = (x_login_address or "").strip().lower()
    if not addr:
        raise HTTPException(401, "missing login address")
    return addr


@api.get("/points")
async def points_get(address: str = Header(default="", alias="X-Login-Address")) -> Dict[str, Any]:
    address = (address or "").strip().lower()
    if not address:
        raise HTTPException(401, "missing login address")
    return {
        "balance": await asyncio.to_thread(points_model.balance, address),
        "config": cfg.points_public(),
        "history": await asyncio.to_thread(points_model.history, address, 50),
    }


def _credits_to_inj(body: Dict[str, Any]) -> float:
    rate = cfg.points_rate("INJ") or 100.0
    if body.get("credits") is not None:
        return round(float(body["credits"]) / rate, 6)
    return float(body.get("amount") or 0)


@api.post("/points/deposit/build")
async def points_deposit_build(request: Request, address: str = Header(default="", alias="X-Login-Address")) -> Dict[str, Any]:
    address = (address or "").strip().lower()
    treasury = cfg.points_treasury()
    if not treasury:
        raise HTTPException(400, "top-up address not configured")
    body = await request.json()
    sender_inj = str(body.get("sender_inj") or "").strip()
    pubkey = str(body.get("pubkey") or "").strip()
    amount = _credits_to_inj(body)
    if not (sender_inj and pubkey) or amount <= 0:
        raise HTTPException(400, "missing sender/pubkey/amount")
    network = cfg.points_treasury_network()
    try:
        out = await asyncio.to_thread(inj_chain.deposit_build, network, sender_inj, treasury, amount, pubkey)
    except Exception as e:
        raise HTTPException(400, f"could not prepare the deposit: {str(e)[:160]}")
    if address:
        await asyncio.to_thread(deposits.remember_sender, sender_inj, "", address)
    out["treasury"] = treasury
    out["amount_inj"] = amount
    return out


@api.post("/points/deposit/submit")
async def points_deposit_submit(request: Request, address: str = Header(default="", alias="X-Login-Address")) -> Dict[str, Any]:
    address = (address or "").strip().lower()
    body = await request.json()
    bb = str(body.get("bodyBytes") or ""); ai = str(body.get("authInfoBytes") or ""); sig = str(body.get("signature") or "")
    if not (bb and ai and sig):
        raise HTTPException(400, "missing signed transaction parts")
    network = cfg.points_treasury_network()
    try:
        res = await asyncio.to_thread(inj_chain.broadcast_signed, network, bb, ai, sig)
    except Exception as e:
        emsg = str(e).lower()
        if "spendable balance" in emsg or "insufficient" in emsg:
            raise HTTPException(400, "insufficient INJ in wallet (need the amount + a little gas)")
        raise HTTPException(400, "deposit broadcast failed, please try again")
    await asyncio.sleep(3)
    credited = {}
    try:
        credited = await asyncio.to_thread(deposits.scan_for_user, address)
    except Exception:
        pass
    return {"ok": True, "txhash": res.get("txhash", ""),
            "credited_points": credited.get("credited_points", 0.0),
            "balance": await asyncio.to_thread(points_model.balance, address),
            "history": await asyncio.to_thread(points_model.history, address, 50)}


@api.post("/points/scan")
async def points_scan(address: str = Header(default="", alias="X-Login-Address")) -> Dict[str, Any]:
    """Scan recent transfer RECORDS to the treasury SENT BY this user and credit
    them (deduped by txhash). Never reads the treasury balance."""
    address = (address or "").strip().lower()
    credited = {}
    try:
        credited = await asyncio.to_thread(deposits.scan_for_user, address)
    except Exception as e:
        print(f"[inj] manual scan failed for {address}: {e!r}")
    return {"ok": True,
            "credited_points": credited.get("credited_points", 0.0),
            "balance": await asyncio.to_thread(points_model.balance, address),
            "history": await asyncio.to_thread(points_model.history, address, 50)}
