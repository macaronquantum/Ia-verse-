from __future__ import annotations


def run(params: dict) -> dict:
    return {"status": "simulated", "exchange": params.get("exchange", "binance"), "symbol": params.get("symbol", "BTC/USDT")}
