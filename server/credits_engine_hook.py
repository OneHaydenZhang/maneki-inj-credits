"""How the (closed-source) agent engine spends INJ credits — illustrative.

The proprietary multi-agent trading engine is NOT part of this repository. This
file documents the ONLY two touch-points it has with the credit/settlement layer,
so the spend side is fully understandable in isolation:

  1. START preflight — refuse to launch an agent that can't pay its first tick.
  2. PER-TICK debit  — every decision tick burns `points_per_tick`; out of credits
     → the agent auto-stops (it literally can't afford to think).

This is the "pay-per-decision" primitive: each autonomous decision is metered and
settled in INJ credits. The functions below are real and runnable against the
ledger in this repo; the surrounding agent loop is shown only as a comment.
"""
from __future__ import annotations

from . import points_model, points_config


def can_start(address: str) -> bool:
    """Start-preflight. An agent that cannot afford a single tick must not run.
    The API layer turns a False here into an HTTP 402 ("top up first")."""
    ppt = points_config.points_per_tick()
    return ppt <= 0 or points_model.balance(address) + 1e-9 >= ppt


def charge_one_tick(address: str, *, note: str = "agent decision tick") -> bool:
    """Called once per decision tick by the agent loop. Returns False when the
    wallet is out of credits — the loop should then stop the agent."""
    cost = points_config.points_per_tick()
    if cost <= 0:
        return True
    return points_model.try_debit(address, cost, kind="tick", note=note)


# ── Illustrative agent loop (the real engine is closed-source) ───────────────
#
#   if not can_start(address):
#       raise HTTPException(402, "Out of INJ credits — top up first")
#
#   while agent.running:
#       if not charge_one_tick(address):        # ← settle one decision on Injective credits
#           agent.stop(reason="out of INJ credits")
#           break
#       ctx      = build_market_context(symbol)
#       decision = llm_decide(ctx, persona)     # the "thinking" the tick paid for
#       execute(decision)                       # perps execution (pluggable venue)
#       sleep(interval)
