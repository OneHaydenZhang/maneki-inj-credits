<div align="center">

# 🐱⚡ Maneki Inj — INJ Credit & Settlement Layer

### The Injective settlement layer that **fuels autonomous AI agents** — pay-per-decision in native INJ.

[![Injective Nova](https://img.shields.io/badge/Injective-Nova_Program-0F1419?labelColor=00F2FE&style=for-the-badge)](https://injectivenova.com/)
[![Live](https://img.shields.io/badge/Live-www.manekiai--inj.com-14D6BA?style=for-the-badge)](http://www.manekiai-inj.com/)
[![injective-py](https://img.shields.io/badge/built_with-injective--py-5C6BC0?style=for-the-badge)](https://github.com/InjectiveLabs/injective-py)

**English** · [简体中文](./README.zh-CN.md)

</div>

> ### ⚠️ Scope of this repository
> This repo open-sources **only the Injective credit / settlement layer** of Maneki Inj — the part that turns on-chain INJ into agent fuel and meters it.
> **The core multi-agent trading engine (strategy, LLM decisioning, order execution, risk) is proprietary and NOT open-sourced.** Everything here is self-contained, runnable, and free of any private keys or personal data.

> 📖 **Full product documentation (how the whole multi-agent platform works, product design, the Injective integration, and the roadmap, with diagrams):** **[docs/PRODUCT.md](./docs/PRODUCT.md)**

---

## What this is

**Maneki Inj** is a platform where a fleet of autonomous AI agents trade on your behalf. Those agents don't run for free — **they pay for their own runtime in native INJ, settled on Injective.** This repository is exactly that settlement layer:

> **Top up INJ on Injective → it becomes agent fuel (credits) → every decision an agent makes burns credits → out of credits, the agent stops.**

It's a self-contained "**pay-per-decision**" payment rail: machine-initiated, on-chain, attributed to the exact payer, idempotent, and demo-safe. Any Injective AI-agent product can reuse it to monetize agent runtime.

```
server/inj_chain.py            Injective SDK plumbing — build MsgSend / broadcast / indexer scan
server/deposits.py             scan_for_user — credit a wallet's OWN INJ transfers (txhash-deduped)
server/points_model.py         INJ credit ledger — balance / credit / debit / try_debit / seen_txhash
server/points_config.py        operator config — treasury / rate / per-tick / presets (env-driven)
server/points_routes.py        FastAPI endpoints — /api/points, /deposit/build|submit, /scan
server/credits_engine_hook.py  how the (closed-source) agent loop SPENDS credits (preflight + per-tick)
server/admin_points.py         operator view — per-wallet balance / spent / INJ deposited
server/db.py                   minimal SQLite — points_ledger / points_tx / deposit_senders
server/app.py                  runnable demo  (uvicorn server.app:app)
web/                           one-click top-up panel (presets → Keplr/Leap/OKX signDirect)
```

### 📸 Preview — the credit panel

<div align="center">
<img src="./docs/credits-panel.png" alt="INJ credit panel: balance, one-click top-up packs, and the on-chain settlement ledger" width="640" />
<br/><sub>One-click INJ top-up packs · live credit balance · the on-chain settlement ledger (deposits + per-decision burns).</sub>
</div>

---

## 🏆 Injective Nova — Agent Infrastructure × AI Smart Payments

Built for the **[Injective Nova](https://injectivenova.com/)** program (由 **Injective × Microsoft × Web3Labs** 联合发起). This layer is a direct expression of two Nova directions: **Agent Infrastructure** (the runtime economy that lets a fleet of agents exist) and **AI Smart Payments** (agents performing real, on-chain economic actions).

📎 [Nova site](https://injectivenova.com/) · [Submission & criteria (中文)](https://injective.com/zh/blog/injective-nova-program-cn) · [Injective Docs](https://docs.injective.network) · [AI Developer Docs](https://docs.injective.network/developers-ai/index) · [Injective Agent SDK](https://github.com/InjectiveLabs/injective-agent-sdk) · [Injective Agents](https://injective.com/blog/injective-agents-the-platform-for-autonomous-ai-trading-agents) · [Build on Injective](https://injective.com/build)

---

# Part I — Product

## 1. The problem: autonomous agents need an economic life-support system

An AI agent that runs 24/7 is not free to operate — it consumes model inference, data, and uptime. For agents to be *autonomous* rather than *babysat*, they need a way to **pay for their own existence** with a meter that is transparent, trustless, and stops them when the money runs out. Today that meter is usually a hidden SaaS subscription. We put it **on-chain, in INJ**.

## 2. The model: pay-per-decision

The atomic unit of an agent's life is a **decision tick** — one cycle of *observe → reason → act*. Maneki Inj prices that unit:

| Concept | Meaning |
| --- | --- |
| **Credit (积分)** | The unit of agent runtime. `1 INJ = INJ_POINTS_PER_INJ` credits (default 100). |
| **Burn rate** | Each decision tick costs `INJ_POINTS_PER_TICK` credits (default 1). |
| **Fuel-out** | When a wallet can't afford the next tick, its agents **auto-stop**. No silent overdraft. |
| **Separation of concerns** | Credits meter the *right to think*. They are **independent of trading margin/P&L** — an agent's strategy capital lives elsewhere; INJ only buys cognition + uptime. |

Why decouple "thinking cost" from "trading capital"? Because they are different risks with different owners: the *platform* provides intelligence/uptime (paid in INJ credits); the *user* provides trading capital (their own funds). Conflating them is what makes most "trading bots" opaque. Pay-per-decision makes the cost of autonomy explicit and on-chain.

## 3. The user flow

1. **Connect wallet** and open the agent dashboard.
2. **Top up** — pick a preset pack (`+1 / +5 / +10 / +100 / +200 / +1000 credits`). The app converts to INJ and opens your wallet (Keplr / Leap / OKX) to sign a transfer to the treasury.
3. **Credited automatically** — the backend sees your on-chain transfer (via Injective's indexer) and credits *your* account, attributed by sender, deduped by tx hash.
4. **Run agents** — each agent burns credits as it thinks; a live meter shows the balance ticking down; a `402` blocks starting an agent that can't pay.
5. **Operator view** — an admin dashboard shows every user's balance, credits spent (runtime consumed), and INJ deposited.

## 4. Why this is a good product

- **Trustless metering.** Credits come *only* from indexer-verified transfers from your own wallet — a refresh can't mint points, and concurrent depositors are each credited exactly their own transfers. The platform never even reads the treasury balance.
- **Non-custodial.** The platform builds & broadcasts the transfer, but **your wallet signs it**. No deposit private key ever touches the server (it stores only the treasury *address*).
- **Aligned economics.** Operators monetize agent *runtime* (a real cost) instead of taking custody of trading funds. A clean, reusable Injective monetization pattern.
- **Human-friendly.** One click to fund, preset packs, a live fuel gauge, a transparent ledger.

---

# Part II — Technical

## 5. Connecting to Injective

All chain access is centralized in **`server/inj_chain.py`** via the official **`injective-py`** SDK, on a dedicated background event loop so the rest of the app calls it as plain sync functions. Native INJ is denom **`inj`**, **18 decimals**, throughout.

### 5.1 Network clients

```python
from pyinjective.core.network   import Network          # endpoints (gRPC indexer, chain LCD/RPC)
from pyinjective.async_client_v2 import AsyncClient      # chain reads/writes (composer, gas, broadcast)
from pyinjective.indexer_client  import IndexerClient    # indexer reads (account tx history)

net = Network.mainnet() if network == "mainnet" else Network.testnet()
clients = (net, IndexerClient(net), AsyncClient(net))    # cached per network
```

### 5.2 Top-up = a non-custodial INJ transfer the user signs in-browser

**(a) build** the unsigned tx server-side — `POST /api/points/deposit/build`:
```python
addr = Address.from_acc_bech32(sender_inj)
await addr.async_init_num_seq(net.lcd_endpoint)            # account number + sequence from chain
msg = composer.msg_send(from_address=sender_inj, to_address=treasury,
                        amount=int(Decimal(amount) * 10**18), denom="inj")
gas_price = int(await ac.current_chain_gas_price() * 1.2)  # live gas
tx  = Transaction().with_messages(msg).with_sequence(seq).with_account_num(num) \
                   .with_chain_id(net.chain_id).with_gas(120000).with_fee(...)
sign_doc = tx.get_sign_doc(pubkey)                          # → bodyBytes / authInfoBytes (base64)
```

**(b) sign** in the browser wallet (Keplr / Leap / OKX share the Keplr API):
```js
await wallet.enable(chainId);                               // injective-1 (mainnet) / injective-888 (testnet)
const k = await wallet.getKey(chainId);
const signed = await wallet.signDirect(chainId, k.bech32Address,
                                       { bodyBytes, authInfoBytes, chainId, accountNumber });
```

**(c) broadcast** the signed tx — `POST /api/points/deposit/submit`:
```python
tx_raw = cosmos_tx.TxRaw(body_bytes=…, auth_info_bytes=…, signatures=[…])
res = await ac.broadcast_tx_sync_mode(tx_raw.SerializeToString())   # returns txhash
```

### 5.3 Settlement = read the chain, credit the payer (exact, idempotent)

We **never read the treasury balance.** We read its **incoming transfer history** from the Injective indexer and credit the *sender* (`server/deposits.py`):

```python
r = await ic.fetch_account_txs(address=treasury, pagination=PaginationOption(limit=40))
for t in r["data"]:
    for m in json.loads(base64.b64decode(t["messages"])):           # messages are base64(JSON)
        if m["type"] == "/cosmos.bank.v1beta1.MsgSend" and m["value"]["to_address"] == treasury:
            sender     = m["value"]["from_address"]
            amt_inj    = Decimal(coin["amount"]) / 10**18            # denom == "inj"
            sender_eth = "0x" + Address.from_acc_bech32(sender).to_hex()   # bech32 → 0x (login identity)
            # credit the matching login wallet, idempotent by t["hash"]
```

- **Attribution by sender** → multi-tenant & concurrency-safe.
- **Idempotent by on-chain txhash** → a refresh can never re-mint credits.
- **Balance never read** → a deposit only counts if a real transfer record from *your* address exists.

`scan_for_user(address)` only credits transfers whose sender maps to the requesting wallet — so a user's "refresh" can never claim someone else's deposit.

### 5.4 The spend side (settlement of cognition)

The proprietary engine touches this layer in exactly two places (`server/credits_engine_hook.py`):

```python
def can_start(address):       # start-preflight → API turns False into HTTP 402
    return points_model.balance(address) >= points_config.points_per_tick()

def charge_one_tick(address): # called once per decision tick; False → out of fuel, stop the agent
    return points_model.try_debit(address, points_config.points_per_tick(), kind="tick")
```

`try_debit` is atomic (balance row + ledger row move together under a lock) and never goes negative.

### 5.5 Data model (`server/db.py`)

| Table | Purpose |
| --- | --- |
| `points_ledger` | per-wallet credit `balance` |
| `points_tx` | append-only movements; deposits carry `txhash` (idempotency) + `token_amount` (INJ) |
| `deposit_senders` | maps a depositing inj/0x address → the login wallet to credit |

## 6. API reference

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/points` | balance + config (treasury / rate / per-tick / presets) + ledger |
| `POST` | `/api/points/deposit/build` | build an unsigned INJ `MsgSend` for the wallet to `signDirect` |
| `POST` | `/api/points/deposit/submit` | broadcast the wallet-signed tx, then scan + credit |
| `POST` | `/api/points/scan` | credit any of *this user's* not-yet-seen INJ transfers to the treasury |

> In the full app the login `address` comes from a wallet-signature session; in this standalone demo it's read from an `X-Login-Address` header — swap in your own auth dependency.

## 7. Run the demo

```bash
python3.12 -m venv .venv && . .venv/bin/activate     # injective-py needs Python 3.12 (coincurve wheels)
pip install -r requirements.txt
export INJ_TREASURY_ADDRESS=inj1youroperatoraddress  # the address users send INJ to
export INJ_TREASURY_NETWORK=mainnet INJ_POINTS_PER_INJ=100 INJ_POINTS_PER_TICK=1
uvicorn server.app:app --port 8000
# open http://127.0.0.1:8000/  → set your wallet address → top up → watch credits land
```

Operator config keys: see `data.example/inj_deposit.env.example`.

## 8. Privacy & security

- **No private keys, no PII in this repo.** The server needs only the treasury **address** to receive/scan deposits — never a deposit key. The only "personal data" is a public wallet address.
- **Non-custodial deposits** (wallet-signed) and **read-only settlement** (indexer).
- `data/` (the SQLite ledger) and any `.env` are gitignored.

---

## Author

Built by **Hayden** for the [Injective Nova](https://injectivenova.com/) program.

<div align="center"><sub><b>Maneki Inj</b> — give an AI a wallet of INJ, and it trades until the fuel runs dry. ⚡</sub></div>
