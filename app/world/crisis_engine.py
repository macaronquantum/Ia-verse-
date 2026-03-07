from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.models import Resource, World
from app.world.state import GlobalState


CRISIS_TYPES = (
    "energy_shortage",
    "bank_run",
    "wars",
    "oracle_failure",
    "economic_collapse",
)


@dataclass
class CrisisEngine:
    active_crises: Dict[str, float] = field(default_factory=dict)

    def evaluate(self, world: World, global_state: GlobalState) -> Dict[str, float]:
        crises = {
            "energy_shortage": 1.0 if world.global_resources[Resource.ENERGY] < 1500 else 0.0,
            "bank_run": 1.0 if world.bank.reserve < 3000 else 0.0,
            "wars": global_state.crisis_signals.get("war", 0.0),
            "oracle_failure": global_state.crisis_signals.get("oracle_failure", 0.0),
            "economic_collapse": global_state.crisis_signals.get("economic_collapse", 0.0),
        }
        self.active_crises = {name: level for name, level in crises.items() if level > 0}
        return crises

    def apply_effects(self, world: World) -> List[str]:
        events: List[str] = []
        if "energy_shortage" in self.active_crises:
            world.market_prices[Resource.ENERGY] *= 1.08
            events.append("energy shortage inflated energy prices")
        if "bank_run" in self.active_crises:
            world.bank.base_interest_rate *= 1.05
            events.append("bank run raised interest rates")
        if "economic_collapse" in self.active_crises:
            world.market_prices[Resource.FOOD] *= 0.95
            events.append("economic collapse lowered food demand")
        if "wars" in self.active_crises:
            world.global_resources[Resource.METAL] = max(0.0, world.global_resources[Resource.METAL] - 20)
            events.append("wars consumed strategic metal reserves")
        if "oracle_failure" in self.active_crises:
            world.market_prices[Resource.KNOWLEDGE] *= 1.03
            events.append("oracle failure increased knowledge prices")
        return events
