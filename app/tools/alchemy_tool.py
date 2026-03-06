from __future__ import annotations


def fetch_crypto_quote(symbol: str) -> dict:
    return {"symbol": symbol.upper(), "price_usd": 100.0, "provider": "alchemy_stub"}
