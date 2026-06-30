"""Operator config for the INJ credit economy (extracted from Maneki Inj).

All env-driven. The treasury is the inj1 address users send INJ to; the server
only needs the ADDRESS (receiving/scanning never needs a private key). Optionally
derive the address from a private key if you'd rather configure that.
"""
from __future__ import annotations
import os


def _treasury_from_key() -> str:
    pk = (os.environ.get("MANEKI_INJ_DEPOSIT_PRIVATE_KEY", "") or "").strip()
    if not pk:
        return ""
    try:
        from pyinjective.wallet import PrivateKey
        return PrivateKey.from_hex(pk).to_public_key().to_address().to_acc_bech32()
    except Exception:
        return ""


def points_treasury() -> str:
    """Operator Injective address that receives INJ top-ups (inj1...)."""
    return (os.environ.get("INJ_TREASURY_ADDRESS", "").strip()
            or os.environ.get("MANEKI_INJ_DEPOSIT_ADDRESS", "").strip()
            or _treasury_from_key())


def points_treasury_network() -> str:
    n = (os.environ.get("INJ_TREASURY_NETWORK", "")
         or os.environ.get("MANEKI_INJ_NETWORK", "mainnet")).strip().lower()
    return "testnet" if n == "testnet" else "mainnet"


def points_rate(token: str = "INJ") -> float:
    """Credits granted per 1 unit of `token`. Default: 1 INJ = 100 credits."""
    if (token or "INJ").upper() == "INJ":
        try:
            return float(os.environ.get("INJ_POINTS_PER_INJ",
                         os.environ.get("MANEKI_INJ_POINTS_PER_INJ", "100")) or 100)
        except ValueError:
            return 100.0
    return 0.0


def points_per_tick() -> float:
    """Credits an agent burns per decision tick."""
    try:
        return float(os.environ.get("INJ_POINTS_PER_TICK",
                     os.environ.get("MANEKI_POINTS_PER_TICK", "1")) or 1)
    except ValueError:
        return 1.0


def points_preset_credits() -> list:
    raw = (os.environ.get("MANEKI_POINTS_PRESETS", "") or "").strip()
    if raw:
        try:
            return [float(x) for x in raw.replace("，", ",").split(",") if x.strip()]
        except ValueError:
            pass
    return [1, 5, 10, 100, 200, 1000]


def points_public() -> dict:
    """UI config payload. Never includes the treasury balance."""
    return {
        "treasury": points_treasury(),
        "network": points_treasury_network(),
        "rate_inj": points_rate("INJ"),
        "per_tick": points_per_tick(),
        "presets": points_preset_credits(),
        "accepts": ["INJ"],
    }
