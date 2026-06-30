"""Injective chain plumbing for the INJ → 积分 top-up (ported from inj_ai).

Everything talks to Injective via injective-py on a single background event loop,
so the rest of the app can call these as plain sync functions from worker threads
(`asyncio.to_thread(inj_chain.xxx, ...)`).

Three primitives power the non-custodial top-up:
  • deposit_build      — build an unsigned native-INJ MsgSend (user → treasury)
  • broadcast_signed   — broadcast the wallet-signed TxRaw, return its txhash
  • fetch_incoming_inj — read the treasury's incoming INJ MsgSend transfers so the
                         scanner can credit the SENDER (exact attribution, txhash-deduped)

injective-py is imported lazily so the server boots even when it's absent.
"""
from __future__ import annotations

import asyncio
import threading
from decimal import Decimal
from typing import Any, Dict, List, Tuple


class ChainError(Exception):
    pass


_loop = None
_loop_lock = threading.Lock()
_CLIENTS: Dict[str, Tuple[Any, Any, Any]] = {}   # network -> (Network, IndexerClient, AsyncClient)


def _ensure_loop():
    global _loop
    if _loop is None:
        with _loop_lock:
            if _loop is None:
                loop = asyncio.new_event_loop()
                threading.Thread(target=loop.run_forever, name="inj-loop", daemon=True).start()
                _loop = loop
    return _loop


def _run(coro, timeout: float = 40.0):
    return asyncio.run_coroutine_threadsafe(coro, _ensure_loop()).result(timeout)


async def _aclients(network: str):
    if network not in _CLIENTS:
        from pyinjective.core.network import Network
        from pyinjective.async_client_v2 import AsyncClient
        from pyinjective.indexer_client import IndexerClient
        net = Network.mainnet() if network == "mainnet" else Network.testnet()
        _CLIENTS[network] = (net, IndexerClient(net), AsyncClient(net))
    return _CLIENTS[network]


def _pubkey_from_b64(pubkey_b64: str):
    """Wrap a wallet-provided compressed secp256k1 pubkey (base64) as a PublicKey."""
    import base64, hashlib
    from ecdsa import VerifyingKey, SECP256k1
    from pyinjective.wallet import PublicKey
    raw = base64.b64decode(pubkey_b64)
    pk = PublicKey(_error_do_not_use_init_directly=True)
    pk.verify_key = VerifyingKey.from_string(raw, curve=SECP256k1, hashfunc=hashlib.sha256)
    return pk


# ------------------------------------------------------- deposit build ------

async def _adeposit_build(network: str, sender_inj: str, to_address: str, amount_inj: float, pubkey_b64: str):
    import base64
    from pyinjective.transaction import Transaction
    from pyinjective.wallet import Address
    net, _, ac = await _aclients(network)
    composer = await ac.composer()
    addr = Address.from_acc_bech32(sender_inj)
    await addr.async_init_num_seq(net.lcd_endpoint)
    num, seq = addr.get_number(), addr.get_sequence()
    amt = int(Decimal(str(amount_inj)) * (Decimal(10) ** 18))
    msg = composer.msg_send(from_address=sender_inj, to_address=to_address, amount=amt, denom="inj")
    gp = int(await ac.current_chain_gas_price() * 1.2)
    gas = 120000
    fee = [composer.coin(amount=gp * gas, denom="inj")]
    pub = _pubkey_from_b64(pubkey_b64)
    tx = (Transaction().with_messages(msg).with_sequence(seq).with_account_num(num)
          .with_chain_id(net.chain_id).with_gas(gas).with_fee(fee).with_memo(""))
    sd = tx.get_sign_doc(pub)
    return {
        "bodyBytes": base64.b64encode(sd.body_bytes).decode(),
        "authInfoBytes": base64.b64encode(sd.auth_info_bytes).decode(),
        "accountNumber": str(num),
        "chainId": net.chain_id,
    }


def deposit_build(network: str, sender_inj: str, to_address: str, amount_inj: float, pubkey_b64: str):
    return _run(_adeposit_build(network, sender_inj, to_address, amount_inj, pubkey_b64), timeout=40)


# ------------------------------------------------------- broadcast ----------

def _tx_outcome(res: Any) -> Tuple[bool, str, str]:
    """Normalize a broadcast result -> (ok, raw_log, txhash)."""
    tr = getattr(res, "tx_response", None) or (res.get("tx_response") if isinstance(res, dict) else None) or res
    def g(o, k):
        return getattr(o, k, None) if not isinstance(o, dict) else o.get(k)
    code = g(tr, "code") or 0
    txh = g(tr, "txhash") or g(tr, "txHash") or ""
    raw = g(tr, "raw_log") or g(tr, "rawLog") or ""
    try:
        ok = int(code) == 0
    except (TypeError, ValueError):
        ok = code in (0, None, "0")
    return ok, str(raw or ""), str(txh or "")


async def _abroadcast_signed(network: str, body_b64: str, authinfo_b64: str, signature_b64: str):
    import base64
    from pyinjective.proto.cosmos.tx.v1beta1 import tx_pb2 as cosmos_tx
    _, _, ac = await _aclients(network)
    tx_raw = cosmos_tx.TxRaw(
        body_bytes=base64.b64decode(body_b64),
        auth_info_bytes=base64.b64decode(authinfo_b64),
        signatures=[base64.b64decode(signature_b64)],
    )
    res = await ac.broadcast_tx_sync_mode(tx_raw.SerializeToString())
    ok, raw, txh = _tx_outcome(res)
    if not ok:
        raise ChainError(raw or "broadcast failed")
    return {"status": "ok", "txhash": txh}


def broadcast_signed(network: str, body_b64: str, authinfo_b64: str, signature_b64: str):
    return _run(_abroadcast_signed(network, body_b64, authinfo_b64, signature_b64), timeout=60)


# ------------------------------------------------ incoming INJ scan ---------

async def _aincoming_inj(network: str, treasury_inj: str, limit: int) -> List[Dict[str, Any]]:
    """Recent incoming native-INJ MsgSend transfers TO `treasury_inj`:
    [{txhash, sender_eth, sender_inj, amount_inj}]. We only ever read the treasury's
    INCOMING transfers — never expose its balance."""
    import base64, json as _json
    from pyinjective.wallet import Address
    from pyinjective.client.model.pagination import PaginationOption
    _, ic, _ = await _aclients(network)
    r = await ic.fetch_account_txs(address=treasury_inj, pagination=PaginationOption(limit=limit))
    out: List[Dict[str, Any]] = []
    for t in (r.get("data") or []):
        if str(t.get("code", 0)) not in ("0", "None", ""):
            continue
        txh = t.get("hash") or ""
        raw = t.get("messages")
        try:
            msgs = _json.loads(base64.b64decode(raw)) if isinstance(raw, str) else (raw or [])
        except Exception:
            continue
        for m in msgs:
            if (m.get("type") or "") != "/cosmos.bank.v1beta1.MsgSend":
                continue
            v = m.get("value") or {}
            if (v.get("to_address") or "") != treasury_inj:
                continue
            sender = v.get("from_address") or ""
            if not sender or sender == treasury_inj:
                continue
            amt_inj = 0.0
            for c in (v.get("amount") or []):
                if c.get("denom") == "inj":
                    try:
                        amt_inj += float(Decimal(str(c.get("amount") or 0)) / Decimal(10) ** 18)
                    except Exception:
                        pass
            if amt_inj <= 0:
                continue
            try:
                sender_eth = "0x" + Address.from_acc_bech32(sender).to_hex()
            except Exception:
                sender_eth = ""
            out.append({"txhash": txh, "sender_eth": sender_eth.lower(),
                        "sender_inj": sender, "amount_inj": amt_inj})
    return out


def fetch_incoming_inj(network: str, treasury_inj: str, limit: int = 40) -> List[Dict[str, Any]]:
    return _run(_aincoming_inj(network, treasury_inj, limit), timeout=40)
