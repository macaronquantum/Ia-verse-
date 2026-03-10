from __future__ import annotations

from app.data.market_intelligence import MarketIntelligence


def run(params: dict) -> dict:
    intel = MarketIntelligence()
    return intel.analyze_equity(params.get("ticker", "AAPL"))
