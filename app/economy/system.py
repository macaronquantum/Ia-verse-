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


class FXMarket:
    def __init__(self) -> None:
        self._rates: dict[str, float] = {"USD": 1.0, "EUR": 1.1, "JPY": 0.007, "GBP": 1.25}

    def convert(self, sell_ccy: str, buy_ccy: str, amount: float) -> float:
        sell_rate = self._rates.get(sell_ccy, 1.0)
        buy_rate = self._rates.get(buy_ccy, 1.0)
        return amount * sell_rate / buy_rate


class EconomySystem:
    def __init__(self) -> None:
        self.interest_rates: dict[str, float] = {"USD": 0.05, "EUR": 0.04}
        self.fx_market = FXMarket()

    def apply_monetary_policy(self, currency: str, rate_shift: float) -> None:
        current = self.interest_rates.get(currency, 0.05)
        self.interest_rates[currency] = max(0.0, current + rate_shift)
