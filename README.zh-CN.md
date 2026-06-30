<div align="center">

# 🐱⚡ Maneki Inj

### 搭载 **Injective** 作为结算层的 **Maneki AI** 多 Agent 平台

_给 AI agent 一个装着 INJ 的钱包——它自己盯盘、推理、交易，每一个决策都在链上付费，直到燃料耗尽。_

[![Injective Nova](https://img.shields.io/badge/Injective-Nova_Program-0F1419?labelColor=00F2FE&style=for-the-badge)](https://injectivenova.com/)
[![Live](https://img.shields.io/badge/Live-www.manekiai--inj.com-14D6BA?style=for-the-badge)](http://www.manekiai-inj.com/)
[![Built with injective-py](https://img.shields.io/badge/built_with-injective--py-5C6BC0?style=for-the-badge)](https://github.com/InjectiveLabs/injective-py)

[English](./README.md) · **简体中文**

</div>

> 📦 **本仓库是 Maneki Inj 的 Injective 充值 / 结算层，单独抽取成一个独立模块**——即驱动 agent 运行的「链上 INJ 充值 + 积分账本 + 扣费钩子」，单独呈现。完整的多 agent 平台在另一个仓库。
>
> **仓库结构**
> ```
> server/inj_chain.py     Injective SDK 链上原语：充值构建 / 广播 / indexer 扫描
> server/deposits.py      scan_for_user —— 给某钱包自己的 INJ 转账入账（txhash 去重）
> server/points_model.py  INJ 积分账本：balance / credit / debit / try_debit / seen_txhash
> server/points_config.py treasury / 汇率 / 每 tick / 预设档（env 驱动）
> server/points_routes.py FastAPI 接口：/api/points、/deposit/build|submit、/scan
> server/db.py            最小 SQLite（points_ledger / points_tx / deposit_senders）
> server/app.py           可运行 demo（uvicorn server.app:app）
> web/                    一键充值面板（预设档 → Keplr/Leap/OKX signDirect）
> ```

---

> **Maneki AI 是智能层——一支自治交易 Agent 舰队。**
> **Injective 是驱动它的结算层**——每个 agent 的供资、计量、存续，完全用原生 **INJ** 结算。Agent 做出的每一个决策，都是一次链上经济行为。

---

## 🏆 Injective Nova — _Agent 基础设施 × AI 智能支付_

为 **[Injective Nova](https://injectivenova.com/)** 计划打造（由 **Injective × Microsoft × Web3Labs** 联合发起 · _AI × 真实应用场景_）。Maneki Inj 正好落在 Nova 的两个创意方向上：

- **Agent Infrastructure（Agent 基础设施）**——一个真正的多 agent 系统：一个钱包跑一整支相互独立、自我进化的 agent 舰队。
- **AI Smart Payments（AI 智能支付）**——agent 进行真实的链上经济行为：它们用 INJ **为自己的运行付费**，在 Injective 上结算与记账。

| 评估标准 | Maneki Inj 如何回应 |
| --- | --- |
| **创新性** | 全新原语：**按决策付费（pay-per-decision）**——把 Injective 用作一个自治 AI agent 经济体的计量与结算轨道。 |
| **技术实现** | 真实接入 `injective-py`、跑在**主网**（indexer 读 + 非托管 MsgSend 签名 + 广播）；AI 与链能力深度耦合（燃料 ↔ 认知）。 |
| **应用价值** | 让任何人都能部署一支交易 agent 舰队，且有清晰的链上成本模型——零运维、无需盯守。 |
| **产品体验** | 一键钱包充值、预设积分档、实时决策流、中英双语理由——Human-friendly AI。 |
| **生态契合** | 一个通用的结算范式，任何 Injective 上的 AI-agent 产品都能复用来对 agent 运行计费。 |

📎 **参考资源：** [Nova 官网](https://injectivenova.com/) · [提交要求与评估标准（中文）](https://injective.com/zh/blog/injective-nova-program-cn) · [Injective 文档](https://docs.injective.network) · [AI 开发者文档](https://docs.injective.network/developers-ai/index) · [Injective Agent SDK](https://github.com/InjectiveLabs/injective-agent-sdk) · [Injective Agents 介绍](https://injective.com/blog/injective-agents-the-platform-for-autonomous-ai-trading-agents) · [Build on Injective](https://injective.com/build)

---

## 目录

1. [核心论点 — Injective 作为 agent 经济的结算层](#1-核心论点--injective-作为-agent-经济的结算层)
2. [多 Agent 系统架构](#2-多-agent-系统架构核心)
3. [INJ 如何驱动 agent — 结算闭环](#3-inj-如何驱动-agent--结算闭环)
4. [快速开始](#4-快速开始)
5. [如何接入 Injective — 技术细节](#5-如何接入-injective--技术细节)
6. [系统架构与部署](#6-系统架构与部署)
7. [隐私 · 风控 · 技术栈](#7-隐私--风控--技术栈)
8. [作者](#作者)

---

## 1. 核心论点 — Injective 作为 agent 经济的结算层

自治 AI agent 要"成立"，需要两件事：一个**持续思考**的地方，和一个**为之付费**的方式。Maneki Inj 让 Injective 成为这条支付与结算的轨道。

- **INJ 是燃料。** Agent 的心跳就是一次*决策 tick*，每个 tick 烧掉一定 **INJ 积分**。积分归零 → agent 停摆。链在字面意义上驱动着舰队的认知。
- **Injective 是 agent 经济结算之处。** 用户通过发送**原生 INJ** 给 agent 供资；后端经 **Injective indexer** 检测并核对到账，按链上**发送方**精确归属，计入积分账本。这正是字面意义上的 **AI Smart Payments**：机器驱动、链上发生、以 INJ 结算。
- **AI 是核心行动者。** 人只设定人格与预算；之后 agent 自己行动——盯盘、推理、交易、自我修正——直到 INJ 耗尽。

> 永续执行层是可插拔的（MVP 把订单路由到某永续场所）。而每个 agent 运行的**供资、支付与记账，完全发生在 Injective 上**——这正是本项目贡献的全新一层。

---

## 2. 多 Agent 系统架构（核心）

**一个钱包 → 一整支舰队。** 一个登录钱包可以**并行**跑多个 agent——甚至同一个标的上跑多个不同策略。每个 agent 都是相互隔离、自我进化的经济行动者。

```text
                        ┌──────────────────────── INJECTIVE （结算与燃料） ─────────────────────────┐
 钱包                    │  原生 INJ ── MsgSend ──▶ treasury ──▶ indexer.fetch_account_txs           │
 (Keplr/Leap/OKX)  ─────│        signDirect                          │  按 SENDER 归属 + txhash 去重 │
        │ 签名登录        └────────────────────────────────────────────┼───────────────────────────────┘
        ▼                                                             ▼  入账  (1 INJ = N 积分)
 ┌──────────────┐      ┌──────────────── 多 agent 引擎 · 按 agent_id 隔离 ──────────────┐
 │  Maneki Inj  │      │  Agent#1 BTC·Navigator ┐                                        │
 │  (FastAPI)   │ ───▶ │  Agent#2 ETH·Hunter    ├─ 每个 = 独立 async 循环：              │
 └──────────────┘      │  Agent#3 SOL·Sentinel  │     tick → 扣 INJ 积分                 │
        ▲              │  Agent#4 BTC·Apex  …   ┘       → 采集 → LLM 决策                │
        │ 按钱包、       │                                 → 风控钳制 → 执行               │
        │ 按 agent      │                                 → Ticket / Decision + 自调 lessons│
        │ 隔离          └────────────┬──────────────────────────────────────────────────┘
        │                  积分耗尽 ─┘ agent 自动停（没燃料）
```

**为什么它是一个"系统"而非脚本：**

| 能力 | 实现 |
| --- | --- |
| **舰队，而非单 bot** | 引擎按 `agent_id`（而非钱包）隔离会话 → 一个钱包可并行无限个 agent，各自一条独立 asyncio 循环。 |
| **每 agent 身份** | 一个 agent = 一个标的 + 一种**人格**（Sentinel / Navigator / Hunter / Apex / 自定义 prompt）+ 自己的周期、杠杆与资金上限。 |
| **完整交易生命周期** | 每个 agent 维护一个 **Ticket**（开→管→平），每个 tick 产出一条 **Decision**（中英双语理由、置信度、观察）——全部落库。 |
| **自我进化** | Agent 从自己平掉的交易中提炼 **lessons** 回灌进下一轮 prompt；周期性 + 停止时生成复盘报告。 |
| **自我修正** | 真实执行反馈（拒单、风控钳制、成交）回放进下一 tick，让 agent 自适应。 |
| **天然安全** | 硬风控（杠杆/名义钳制、kill-switch）、全舰队 LLM 并发上限、重启自动恢复、**燃料耗尽自动停**。 |
| **多租户隔离** | 钱包签名登录（SIWE 风格）；每份密钥/配置/交易/报告按钱包命名空间隔离；签名私钥 Fernet 加密存储。 |

---

## 3. INJ 如何驱动 agent — 结算闭环

```text
┌── 充值  (在 Injective 上) ─────────────────────────────────────────────┐
│ Agent 中心预设档：  [+1] [+5] [+10] [+100] [+200] [+1000 积分]          │
│        ▼ 按 1 INJ = INJ_POINTS_PER_INJ 折算成 INJ                       │
│ 钱包 (Keplr/Leap/OKX) 签 MsgSend  →  treasury (inj1…)                  │
│        ▼                                                               │
│ 后端经 Injective indexer 读取 treasury 的【入账】转账记录              │
│   • 按 SENDER（付款方地址）归属                                         │
│   • 按链上 txhash 幂等去重   ·   从不读取 treasury 余额                 │
│        ▼  给付款方账户入账积分                                          │
└────────────────────────────────────────────────────────────────────────┘
┌── 消耗  (每个 agent，每个 tick) ──────────────────────────────────────┐
│ try_debit(INJ_POINTS_PER_TICK)：                                       │
│   积分 ≥ 成本 → 思考并可能交易   ·   积分 < 成本 → 停止                 │
│ 用 0 积分启动 agent → HTTP 402（请先充值）                              │
└────────────────────────────────────────────────────────────────────────┘
```

**为什么正确且演示安全：** 积分**只**来自经 indexer 核验的、从*你的*钱包到 treasury 的真实转账，并按 txhash 去重——所以刷新永远不会凭空造分，并发充值的人也各记各的。平台只读*入账记录*，从不读 treasury 余额。

---

## 4. 快速开始

```bash
./run.sh                       # 启动多 agent 服务，默认 :4180
# 打开 http://127.0.0.1:4180/   （或线上：http://www.manekiai-inj.com/）
```

1. **连接钱包**——签名登录（不发交易、不花 gas、不接触资金）。
2. **Agent 中心 → 充值 INJ 积分**——预设档会拉起 Keplr / Leap / OKX 发送 INJ，到账自动入账。
3. **Settings** → 你的永续签名私钥（服务端 Fernet 加密）+ 风控限额。
4. **+ New Agent** → 选标的 / 人格 / 周期 → 启动。想跑几个跑几个。
5. 看 **行情台**（行情 + 实时决策流）、**账户总览**、**交易历史**（每个 ticket 的开→管→平→复盘）。

**运营方配置**（本地 `data/maneki_inj.env`，`run.sh` 自动加载；模板见 `data.example/inj_deposit.env.example`）：

```bash
INJ_TREASURY_ADDRESS=inj1youroperatoraddress   # 用户充值的收款地址（服务器只存地址）
INJ_TREASURY_NETWORK=mainnet
INJ_POINTS_PER_INJ=100                          # 1 INJ = 100 积分
INJ_POINTS_PER_TICK=1                           # 每个 agent tick 烧多少积分
HYPERPILOT_OPENROUTER_KEY=sk-or-...             # 全舰队共享的 LLM key
MANEKI_ADMIN_TOKEN=...                          # 管理后台令牌（/admin.html）
```

---

## 5. 如何接入 Injective — 技术细节

所有 Injective 访问都集中在 **`server/inj_chain.py`**，经官方 **`injective-py`** SDK，跑在一条专用后台事件循环上，供其余代码以同步函数调用。

### 5.1 网络客户端

```python
from pyinjective.core.network   import Network          # 端点（gRPC indexer、chain LCD/RPC）
from pyinjective.async_client_v2 import AsyncClient      # 链读写（composer、gas、广播）
from pyinjective.indexer_client  import IndexerClient    # indexer 读（账户交易历史）

net = Network.mainnet() if network == "mainnet" else Network.testnet()
clients = (net, IndexerClient(net), AsyncClient(net))    # 按网络缓存
```

`INJ_TREASURY_NETWORK` 选 mainnet/testnet，同一套代码两边都跑。原生 INJ 的 denom 是 **`inj`**，**18 位精度**。

### 5.2 充值 = 用户在浏览器里自己签名的非托管 INJ 转账

平台永远拿不到用户私钥——用户在自己钱包里签一笔 Cosmos `MsgSend`。三步：

**(a) 构建** 未签名交易（服务端，`/api/points/deposit/build`）：
```python
addr = Address.from_acc_bech32(sender_inj)
await addr.async_init_num_seq(net.lcd_endpoint)            # 从链上取账号 + 序列号
msg = composer.msg_send(from_address=sender_inj, to_address=treasury,
                        amount=int(Decimal(amount) * 10**18), denom="inj")
gas_price = int(await ac.current_chain_gas_price() * 1.2)  # 实时 gas
tx  = Transaction().with_messages(msg).with_sequence(seq).with_account_num(num) \
                   .with_chain_id(net.chain_id).with_gas(120000).with_fee(...)
sign_doc = tx.get_sign_doc(pubkey)                          # → bodyBytes / authInfoBytes (base64)
```

**(b) 签名**（浏览器钱包，Keplr / Leap / OKX 共用 Keplr API）：
```js
await wallet.enable(chainId);                               // injective-1（主网）/ injective-888（测试网）
const k = await wallet.getKey(chainId);
const signed = await wallet.signDirect(chainId, k.bech32Address,
                                       { bodyBytes, authInfoBytes, chainId, accountNumber });
```

**(c) 广播**（服务端，`/api/points/deposit/submit`）：
```python
tx_raw = cosmos_tx.TxRaw(body_bytes=…, auth_info_bytes=…, signatures=[…])
res = await ac.broadcast_tx_sync_mode(tx_raw.SerializeToString())   # 返回 txhash
```

### 5.3 结算 = 读链上、给付款方入账（精确、幂等）

我们**从不读 treasury 余额**，而是经 Injective indexer 读它的**入账转账历史**、给*发送方*入账：

```python
r = await ic.fetch_account_txs(address=treasury, pagination=PaginationOption(limit=40))
for t in r["data"]:
    for m in json.loads(base64.b64decode(t["messages"])):           # messages 是 base64(JSON)
        if m["type"] == "/cosmos.bank.v1beta1.MsgSend" and m["value"]["to_address"] == treasury:
            sender     = m["value"]["from_address"]
            amt_inj    = Decimal(coin["amount"]) / 10**18            # denom == "inj"
            sender_eth = "0x" + Address.from_acc_bech32(sender).to_hex()   # bech32 → 0x（登录身份）
            # 给匹配的登录钱包入账，按 t["hash"] 幂等
```

- **按发送方归属** → 多租户、并发安全；两人同时充值各记各的。
- **按链上 txhash 幂等** → 刷新永远不会重复造分。
- **从不读余额** → 只有当存在一条来自*你的*地址的真实转账记录时才算充值成功。

### 5.4 为什么这是对的产品设计

| 取舍 | 理由 |
| --- | --- |
| **用积分，而非按笔扣 INJ** | 把 *agent 运行成本*（认知/在线）与*交易保证金*解耦。INJ 计量的是**思考权**；agent 的盈亏是另一回事——这就是 "AI Smart Payments" 原语：按决策付费。 |
| **单一运营方 treasury** | 链上足迹最小；用户充到一个 `inj1` 地址。按发送方归属即可精确记账，无需每用户地址或 memo。 |
| **浏览器内 signDirect** | 非托管——平台负责构建与广播，用户钱包负责签名。任何充值私钥都不上服务器（只存 treasury **地址**）。 |
| **用 indexer，而非轮询余额** | indexer 给出*转账记录*（谁付的、付了多少、哪笔 tx）——这是入账唯一正确的信号。余额增量无法归属也无法去重。 |
| **燃料耗尽自动停** | 没有 INJ 积分的 agent 字面上付不起下一个决策 → 它停。经济模型和运行模型是同一个模型。 |

### 5.5 代码索引（Injective 面）

| 文件 | Injective 面 |
| --- | --- |
| `server/inj_chain.py` | `Network` · `IndexerClient.fetch_account_txs` · `AsyncClient`（`composer.msg_send`、`current_chain_gas_price`、`broadcast_tx_sync_mode`）· `Address` bech32↔0x |
| `server/deposits.py` | `scan_for_user()`——给某钱包自己的 INJ 转账入账，txhash 去重 |
| `server/points_model.py` | INJ 积分账本：`balance / credit / debit / try_debit / seen_txhash` |
| `server/points_model.py (try_debit, called by the agent loop)` | 多 agent 循环；每 tick `try_debit`（燃料）+ 耗尽自动停 |
| `server/points_routes.py` | `GET /api/points`、`POST /api/points/deposit/build\|submit`、`POST /api/points/scan` |
| `web/credits.js` | Agent 中心充值面板（预设档 → `signDirect`）+ 积分计 |

---

## 6. 系统架构与部署

```text
单进程 FastAPI  (auto_service.app:app)
├─ handlers/        REST API：auth · config · markets · agents · points · portfolio · admin
├─ services/engine.py      多 agent 引擎——每 agent 一条 async 循环；每 tick 扣 INJ 积分
│  services/inj_chain.py   Injective：充值构建 / 广播 / indexer 扫描
│  services/deposits.py    链上 INJ → 积分（按发送方、txhash 去重）
│  services/agent_service.py   合并配置 · 风控钳制 · 自调 lessons
├─ models/   agent · ticket · decision · points · config   (SQLite)
├─ crypto.py / auth.py     Fernet 加密私钥 + 钱包签名登录
└─ web/                    原生 ES-module SPA：行情台 / Agent 中心 / 账户总览 / 交易历史 / 后台
```

**部署：** GCE 虚机上的 systemd 服务（用 `uv` 装 Python 3.12），监听 80 端口，**Cloudflare** 前置到 **[www.manekiai-inj.com](http://www.manekiai-inj.com/)**。更新用 `auto_service/deploy/redeploy.sh`。

---

## 7. 隐私 · 风控 · 技术栈

- **密钥永不进 git。** 每钱包签名私钥在 SQLite 里 Fernet 加密（`HYPERPILOT_MASTER_KEY`）；运营方密钥只存本地 `data/maneki_inj.env` / 服务器 `/etc/maneki-inj.env`（root `600`）。整个 `data/` 被 `.gitignore`，服务器只存 treasury **地址**——**没有任何充值私钥**。
- **代码强制风控：** 杠杆 `min(模型, 用户, 标的)` · 单笔名义封顶 · kill-switch · 连续错误停 · max-ticks · **INJ 积分耗尽自动停**。
- **技术栈：** FastAPI · Uvicorn · **injective-py**（indexer + chain）· eth-account（钱包验签）· cryptography（Fernet）· OpenRouter · 原生 ES-module 前端（无构建）。

---

## 作者

由 **Hayden** 为 [Injective Nova](https://injectivenova.com/) 计划打造。

<div align="center"><sub><b>Maneki Inj</b> — 给 AI 一个装着 INJ 的钱包，它会一直交易到燃料耗尽。⚡</sub></div>
