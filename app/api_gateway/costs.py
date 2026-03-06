from __future__ import annotations

from pydantic import BaseModel


DEFAULT_COSTS = {
    "llm_local": 0.01,
    "llm_openai": 1.0,
    "alchemy_price_query": 0.05,
    "figma_design_export": 0.8,
    "stripe_charge_create": 0.2,
    "google_calendar_create": 0.05,
    "twitter_post": 0.05,
    "solana_tx_broadcast": 0.5,
    "tool_sandbox_second": 0.02,
    "tool_call_base": 0.01,
}


class CostUpdate(BaseModel):
    key: str
    value: float


class CostCatalog:
    def __init__(self) -> None:
        self._costs = dict(DEFAULT_COSTS)

    def all(self) -> dict[str, float]:
        return dict(self._costs)

    def update(self, key: str, value: float) -> None:
        if value < 0:
            raise ValueError("cost must be >= 0")
        self._costs[key] = value

    def get(self, key: str, default: float = 0.0) -> float:
        return self._costs.get(key, default)
