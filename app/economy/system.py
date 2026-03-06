from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import Action
from app.economy.markets import MarketSystem, Order
from app.energy.core import EnergyLedger


@dataclass
class EconomyCoordinator:
    market: MarketSystem
    ledger: EnergyLedger

    def validate_and_apply_action(self, action: Action) -> bool:
        if self.ledger.balance_of(action.actor_id) < action.cost:
            return False
        self.ledger.charge_action(action.actor_id)

        if action.kind == "trade":
            payload = action.payload
            self.market.submit_order(
                Order(
                    agent_id=action.actor_id,
                    market=payload.get("market", "services"),
                    side=payload.get("side", "buy"),
                    quantity=float(payload.get("qty", 1)),
                    limit_price=float(payload.get("limit_price", 10)),
                )
            )
        elif action.kind == "offer_labor":
            self.market.submit_order(Order(action.actor_id, "labor", "sell", float(action.payload.get("hours", 1)), 5.0))
        elif action.kind == "allocate_capital":
            self.market.submit_order(Order(action.actor_id, "capital", "sell", float(action.payload.get("budget", 1)), 12.0))

        return True

    def tick(self) -> dict[str, float]:
        return self.market.tick()
