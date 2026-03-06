from __future__ import annotations

from dataclasses import dataclass


@dataclass
class APIOracle:
    """External world adapter with deterministic stub payloads."""

    async def fetch(self, source: str) -> dict[str, float]:
        if source == "macro_feed":
            return {"inflation": 2.1, "gdp_growth": 1.8}
        if source == "fx_feed":
            return {"usd_index": 102.4}
        return {"signal": 0.0}
