<div align="center">

# 🐱⚡ Maneki Inj

### The **Maneki AI** multi-agent platform, settled on **Injective**.

_Give an AI agent a wallet of INJ — it observes, reasons, and trades on its own, paying for every decision on-chain, until the fuel runs dry._

[![Injective Nova](https://img.shields.io/badge/Injective-Nova_Program-0F1419?labelColor=00F2FE&style=for-the-badge)](https://injectivenova.com/)
[![Live](https://img.shields.io/badge/Live-www.manekiai--inj.com-14D6BA?style=for-the-badge)](http://www.manekiai-inj.com/)
[![Built with injective-py](https://img.shields.io/badge/built_with-injective--py-5C6BC0?style=for-the-badge)](https://github.com/InjectiveLabs/injective-py)

**English** · [简体中文](./README.zh-CN.md)

</div>

> 📦 **This repository is the Injective credit / settlement layer of Maneki Inj, extracted as a standalone module** — the on-chain INJ top-up + credit ledger + spend hook that fuels the agents, in isolation. The full multi-agent platform lives in a separate repo.
>
> **Repository layout**
> ```
> server/inj_chain.py     Injective SDK plumbing: deposit build / broadcast / indexer scan
> server/deposits.py      scan_for_user — credit a wallet's own INJ transfers (txhash-deduped)
> server/points_model.py  INJ credit ledger: balance / credit / debit / try_debit / seen_txhash
> server/points_config.py treasury / rate / per-tick / presets (env-driven)
> server/points_routes.py FastAPI endpoints: /api/points, /deposit/build|submit, /scan
> server/db.py            minimal SQLite (points_ledger / points_tx / deposit_senders)
> server/app.py           runnable demo (uvicorn server.app:app)
> web/                    one-click top-up panel (presets → Keplr/Leap/OKX signDirect)
> ```

---

> **Maneki AI is the intelligence — a fleet of autonomous trading agents.**
> **Injective is the settlement layer that powers them** — every agent is funded, metered, and kept alive entirely in native **INJ**. Each decision an agent makes is an on-chain economic action.

---

## 🏆 Injective Nova — _Agent Infrastructure × AI Smart Payments_

Built for the **[Injective Nova](https://injectivenova.com/)** program (由 **Injective × Microsoft × Web3Labs** 联合发起 · _AI × real-world applications_). Maneki Inj sits squarely on two of Nova's creative directions:

- **Agent Infrastructure** — a true multi-agent system: one wallet runs a whole fleet of independent, self-improving agents.
- **AI Smart Payments** — agents perform real on-chain economic behavior: they *pay for their own runtime* in INJ, settled and accounted on Injective.

| Evaluation criterion | How Maneki Inj answers it |
| --- | --- |
| **Innovation** | A novel primitive: **pay-per-decision** — Injective as the metering & settlement rail for an autonomous AI agent economy. |
| **Technical execution** | Real `injective-py` integration on **mainnet** (indexer reads + non-custodial MsgSend signing + broadcast); deep AI×chain coupling (fuel ↔ cognition). |
| **Use case & impact** | Lets anyone deploy a fleet of trading agents with a clear, on-chain cost model — no infra, no babysitting. |
| **Product & UX** | One-click wallet top-up, preset credit packs, live decision feed, bilingual reasoning — Human-friendly AI. |
| **Ecosystem fit** | Generic settlement pattern any Injective AI-agent product can reuse to monetize agent runtime. |

📎 **Resources:** [Nova site](https://injectivenova.com/) · [Submission & criteria (中文)](https://injective.com/zh/blog/injective-nova-program-cn) · [Injective Docs](https://docs.injective.network) · [AI Developer Docs](https://docs.injective.network/developers-ai/index) · [Injective Agent SDK](https://github.com/InjectiveLabs/injective-agent-sdk) · [Injective Agents](https://injective.com/blog/injective-agents-the-platform-for-autonomous-ai-trading-agents) · [Build on Injective](https://injective.com/build)

---

## Table of contents

1. [The thesis — Injective as the agent economy's settlement layer](#1-the-thesis--injective-as-the-agent-economys-settlement-layer)
2. [Multi-agent system architecture](#2-multi-agent-system-architecture-the-core)
3. [How INJ fuels the agents — the settlement loop](#3-how-inj-fuels-the-agents--the-settlement-loop)
4. [Quick start](#4-quick-start)
5. [Connecting to Injective — technical deep-dive](#5-connecting-to-injective--technical-deep-dive)
6. [System architecture & deployment](#6-system-architecture--deployment)
7. [Privacy, risk & stack](#7-privacy-risk--stack)
8. [Author](#author)

---

## 1. The thesis — Injective as the agent economy's settlement layer

Autonomous AI agents need two things to be *real*: a place to **think continuously**, and a way to **pay for it**. Maneki Inj makes Injective that payment-and-settlement rail.

- **INJ is the fuel.** An agent's heartbeat is a *decision tick*. Every tick burns **INJ credits**. No credits → the agent halts. The chain literally powers the fleet's cognition.
- **Injective is where the agent economy settles.** Users fund agents by sending **native INJ on Injective**; deposits are detected and reconciled through **Injective's indexer**, attributed to the exact payer on-chain, and metered into a credit ledger. This is **AI Smart Payments** in the literal sense: machine-driven, on-chain, settled in INJ.
- **AI as the core actor.** Humans set a persona and a budget; from there the agents act on their own — observe markets, reason, trade, self-correct — until their INJ runs out.

> The perpetual-execution layer is pluggable (the MVP routes orders to a perps venue). The **funding, payment, and accounting of every agent's runtime live entirely on Injective** — that's the novel layer this project contributes.

---

## 2. Multi-agent system architecture (the core)

**One wallet → a whole fleet.** A logged-in wallet runs *many* agents in parallel — even several on the same symbol with different strategies. Each agent is an isolated, self-improving economic actor.

```text
                        ┌──────────────────────── INJECTIVE  (settlement & fuel) ───────────────────────┐
 wallet                 │  native INJ ── MsgSend ──▶ treasury ──▶ indexer.fetch_account_txs              │
 (Keplr/Leap/OKX)  ─────│        signDirect                          │  attribute by SENDER + txhash dedup │
        │ sign-in        └────────────────────────────────────────────┼────────────────────────────────────┘
        ▼                                                             ▼  credit  (1 INJ = N 积分)
 ┌──────────────┐      ┌──────────────── multi-agent engine · keyed by agent_id ───────────────┐
 │  Maneki Inj  │      │  Agent#1 BTC·Navigator ┐                                                │
 │  (FastAPI)   │ ───▶ │  Agent#2 ETH·Hunter    ├─ each = its own async loop:                    │
 └──────────────┘      │  Agent#3 SOL·Sentinel  │     tick → DEBIT INJ credits                   │
        ▲              │  Agent#4 BTC·Apex  …   ┘       → observe → LLM decide                    │
        │ per-wallet,  │                                 → risk-clamp → execute                    │
        │ per-agent    │                                 → Ticket / Decision + self-tuning lessons │
        │ isolation    └────────────┬──────────────────────────────────────────────────────────┘
        │                  out of credits ─┘ agent auto-stops (no fuel)
```

**What makes it a *system*, not a script:**

| Capability | How |
| --- | --- |
| **Fleet, not a bot** | The engine keys sessions by `agent_id` (not by wallet) → unlimited parallel agents per wallet, each an independent asyncio loop. |
| **Per-agent identity** | One agent = one symbol + one **persona** (Sentinel / Navigator / Hunter / Apex / custom prompt) + its own cadence, leverage & capital box. |
| **Full trade lifecycle** | Each agent runs a **Ticket** (open → manage → close) and emits a **Decision** every tick (bilingual reasoning, confidence, observations) — all persisted. |
| **Self-improving** | Agents distill **lessons** from their own closed trades and feed them into the next prompt; periodic + on-stop reflection reports. |
| **Self-correcting** | Real execution feedback (rejects, risk-clamps, fills) is replayed into the next tick so the agent adapts. |
| **Safe by construction** | Hard risk envelope (leverage / notional clamps, kill-switch), fleet-wide LLM concurrency cap, restart-resume of cleanly-running agents, **fuel-out auto-stop**. |
| **Multi-tenant & isolated** | Wallet-signature login (SIWE-style); every key / config / trade / report is namespaced per wallet; signing keys stored Fernet-encrypted. |

---

## 3. How INJ fuels the agents — the settlement loop

```text
┌── TOP UP  (on Injective) ─────────────────────────────────────────────┐
│ Agent-center preset packs:  [+1] [+5] [+10] [+100] [+200] [+1000 积分] │
│        ▼ convert to INJ at 1 INJ = INJ_POINTS_PER_INJ                  │
│ wallet (Keplr/Leap/OKX) signs a MsgSend  →  treasury (inj1…)           │
│        ▼                                                               │
│ backend reads the treasury's INCOMING transfers via Injective indexer  │
│   • attribute by SENDER (the payer's address)                          │
│   • idempotent by on-chain txhash   ·   treasury balance never read    │
│        ▼  credit the payer's account                                   │
└────────────────────────────────────────────────────────────────────────┘
┌── SPEND  (per agent, every tick) ─────────────────────────────────────┐
│ try_debit(INJ_POINTS_PER_TICK):                                        │
│   credits ≥ cost → think & maybe trade   ·   credits < cost → STOP     │
│ starting an agent with 0 credits → HTTP 402 (top up first)            │
└────────────────────────────────────────────────────────────────────────┘
```

**Why it's correct & demo-safe:** credits come **only** from real, indexer-verified transfers from *your* wallet to the treasury, deduped by txhash — so refreshing can never mint points, and concurrent depositors are each credited exactly their own transfers. The platform reads only *incoming transfers*, never the treasury balance.

---

## 4. Quick start

```bash
./run.sh                       # boots the multi-agent service on :4180
# open http://127.0.0.1:4180/   (or the live deployment: http://www.manekiai-inj.com/)
```

1. **Connect wallet** — signature login (no gas, no fund access).
2. **Agent Center → top up INJ credits** — preset packs open Keplr / Leap / OKX to send INJ; auto-credited.
3. **Settings** → your perps signing key (Fernet-encrypted server-side) + risk limits.
4. **+ New Agent** → pick symbol / persona / cadence → launch. Spin up as many as you like.
5. Watch the **Terminal** (markets + live decision flow), **Portfolio**, and **Trade History** (every ticket's open → manage → close → report).

**Operator config** (gitignored `data/maneki_inj.env`, auto-loaded by `run.sh`; template: `data.example/inj_deposit.env.example`):

```bash
INJ_TREASURY_ADDRESS=inj1youroperatoraddress   # where users send INJ (the server holds the ADDRESS only)
INJ_TREASURY_NETWORK=mainnet
INJ_POINTS_PER_INJ=100                          # 1 INJ = 100 credits
INJ_POINTS_PER_TICK=1                           # fuel burned per agent tick
HYPERPILOT_OPENROUTER_KEY=sk-or-...             # shared LLM key for the fleet
MANEKI_ADMIN_TOKEN=...                          # admin panel token  (/admin.html)
```

---

## 5. Connecting to Injective — technical deep-dive

All Injective access is centralized in **`server/inj_chain.py`** via the official **`injective-py`** SDK, on a dedicated background event loop so the rest of the app calls it as plain sync functions.

### 5.1 Network clients

```python
from pyinjective.core.network   import Network          # endpoints (gRPC indexer, chain LCD/RPC)
from pyinjective.async_client_v2 import AsyncClient      # chain reads/writes (composer, gas, broadcast)
from pyinjective.indexer_client  import IndexerClient    # indexer reads (account tx history)

net = Network.mainnet() if network == "mainnet" else Network.testnet()
clients = (net, IndexerClient(net), AsyncClient(net))    # cached per network
```

`INJ_TREASURY_NETWORK` selects mainnet/testnet; the same code path runs on either. Native INJ is denom **`inj`** with **18 decimals**.

### 5.2 Top-up = a non-custodial INJ transfer the user signs in-browser

The user never hands us a key — they sign a Cosmos `MsgSend` in their own wallet. Three steps:

**(a) build** the unsigned tx server-side — `/api/points/deposit/build`:
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

**(c) broadcast** the signed tx — `/api/points/deposit/submit`:
```python
tx_raw = cosmos_tx.TxRaw(body_bytes=…, auth_info_bytes=…, signatures=[…])
res = await ac.broadcast_tx_sync_mode(tx_raw.SerializeToString())   # returns txhash
```

### 5.3 Settlement = read the chain, credit the payer (exact, idempotent)

We **never read the treasury balance.** We read its **incoming transfer history** from the Injective indexer and credit the *sender*:

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

- **Attribution by sender** → multi-tenant & concurrency-safe; two users depositing at once are each credited *their own* transfers.
- **Idempotent by on-chain txhash** → a refresh can never re-mint credits.
- **Balance never read** → a deposit only counts if a real transfer record from *your* address exists.

### 5.4 Why this is the right product design

| Decision | Rationale |
| --- | --- |
| **Credits, not raw INJ-per-trade** | Decouples *agent runtime cost* (cognition/uptime) from *trading margin*. INJ meters the **right to think**; the agent's P&L is separate — the "AI Smart Payments" primitive: pay-per-decision. |
| **One operator treasury** | Minimal on-chain footprint; users top up to a single `inj1` address. Per-sender attribution keeps accounting exact without per-user addresses or memos. |
| **In-browser signDirect** | Non-custodial — the platform builds & broadcasts, but the user's wallet signs. No deposit key ever touches the server (it stores only the treasury **address**). |
| **Indexer, not balance polling** | The indexer yields *transfer records* (who paid, how much, which tx) — the only correct signal for crediting. Balance deltas can't attribute or dedupe. |
| **Fuel-out auto-stop** | An agent with no INJ credits literally cannot afford its next decision → it stops. The economic model and the runtime model are the same model. |

### 5.5 Code map (Injective surface)

| File | Injective surface |
| --- | --- |
| `server/inj_chain.py` | `Network` · `IndexerClient.fetch_account_txs` · `AsyncClient` (`composer.msg_send`, `current_chain_gas_price`, `broadcast_tx_sync_mode`) · `Address` bech32↔0x |
| `server/deposits.py` | `scan_for_user()` — credit a wallet's own INJ transfers, txhash-deduped |
| `server/points_model.py` | INJ credit ledger: `balance / credit / debit / try_debit / seen_txhash` |
| `server/points_model.py (try_debit, called by the agent loop)` | the multi-agent loop; per-tick `try_debit` (fuel) + fuel-out auto-stop |
| `server/points_routes.py` | `GET /api/points`, `POST /api/points/deposit/build\|submit`, `POST /api/points/scan` |
| `web/credits.js` | Agent-center top-up panel (preset packs → `signDirect`) + credits meter |

---

## 6. System architecture & deployment

```text
single-process FastAPI  (auto_service.app:app)
├─ handlers/        REST API: auth · config · markets · agents · points · portfolio · admin
├─ services/engine.py      multi-agent engine — one async loop per agent_id; INJ debit per tick
│  services/inj_chain.py   Injective: deposit build / broadcast / indexer scan
│  services/deposits.py    on-chain INJ → credits (by-sender, txhash-dedup)
│  services/agent_service.py   merge config · risk clamps · self-tuning lessons
├─ models/   agent · ticket · decision · points · config   (SQLite)
├─ crypto.py / auth.py     Fernet-encrypted keys + wallet-signature login
└─ web/                    native ES-module SPA: Terminal / Agents / Portfolio / History / Admin
```

**Deployment:** systemd service on a GCE VM (Python 3.12 via `uv`), bound to port 80, fronted by **Cloudflare** at **[www.manekiai-inj.com](http://www.manekiai-inj.com/)**. Ship updates with `auto_service/deploy/redeploy.sh`.

---

## 7. Privacy, risk & stack

- **Secrets never enter git.** Per-wallet signing keys are Fernet-encrypted in SQLite (`HYPERPILOT_MASTER_KEY`); operator secrets live only in `data/maneki_inj.env` (local) / `/etc/maneki-inj.env` (server, root `600`). The whole `data/` tree is `.gitignore`d, and the server holds the treasury **address** only — **no deposit private key**.
- **Code-enforced risk:** leverage `min(model, user, market)` · notional cap · kill-switch · consecutive-error stop · max-ticks · **INJ-fuel-out auto-stop**.
- **Stack:** FastAPI · Uvicorn · **injective-py** (indexer + chain) · eth-account (wallet auth) · cryptography (Fernet) · OpenRouter · native ES-module front-end (no build step).

---

## Author

Built by **Hayden** for the [Injective Nova](https://injectivenova.com/) program.

<div align="center"><sub><b>Maneki Inj</b> — give an AI a wallet of INJ, and it trades until the fuel runs dry. ⚡</sub></div>
