from __future__ import annotations

def valuation(revenue: float, sentiment: float, liquidity: float) -> float:
    return max(0.0, revenue * 8 + sentiment * 50 + liquidity * 10)
