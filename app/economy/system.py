from __future__ import annotations

from dataclasses import dataclass, field

from app.economy.markets import EquityMarket, FXMarket


@dataclass
class EconomySystem:
    fx_market: FXMarket = field(default_factory=FXMarket)
    equity_market: EquityMarket = field(default_factory=EquityMarket)
    interest_rates: dict[str, float] = field(default_factory=lambda: {"USD": 0.03, "EUR": 0.025, "AFR": 0.06})

    def apply_monetary_policy(self, currency: str, rate_shift: float) -> None:
        self.interest_rates[currency] = max(0.0, self.interest_rates.get(currency, 0.01) + rate_shift)
