from __future__ import annotations

from dataclasses import dataclass

from app.business.metrics import valuation

STAGES = ["Idea", "Prototype", "MVP", "Product", "Traction", "Growth", "Scale", "Unicorn"]


@dataclass
class StartupState:
    name: str
    stage: str = "Idea"
    revenue: float = 0.0
    expenses: float = 0.0
    sentiment: float = 0.0
    liquidity: float = 1.0

    def advance(self) -> str:
        idx = STAGES.index(self.stage)
        if idx < len(STAGES) - 1:
            self.stage = STAGES[idx + 1]
        return self.stage

    @property
    def current_valuation(self) -> float:
        return valuation(self.revenue, self.sentiment, self.liquidity)
