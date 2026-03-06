from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FXMarket:
    rates: dict[tuple[str, str], float] = field(
        default_factory=lambda: {
            ("USD", "EUR"): 0.9,
            ("EUR", "USD"): 1.11,
            ("USD", "AFR"): 14.0,
            ("AFR", "USD"): 0.071,
        }
    )

    def convert(self, from_ccy: str, to_ccy: str, amount: float) -> float:
        if from_ccy == to_ccy:
            return amount
        return amount * self.rates[(from_ccy, to_ccy)]


@dataclass
class EquityMarket:
    prices: dict[str, float] = field(default_factory=dict)
    ownership: dict[str, dict[str, float]] = field(default_factory=dict)

    def issue_primary(self, company_id: str, investor_id: str, shares: float, price: float) -> float:
        self.prices[company_id] = price
        self.ownership.setdefault(company_id, {})
        self.ownership[company_id][investor_id] = self.ownership[company_id].get(investor_id, 0.0) + shares
        return shares * price

    def trade_secondary(self, company_id: str, seller: str, buyer: str, shares: float) -> float:
        held = self.ownership.get(company_id, {}).get(seller, 0.0)
        if held < shares:
            raise ValueError("insufficient shares")
        self.ownership[company_id][seller] -= shares
        self.ownership[company_id][buyer] = self.ownership[company_id].get(buyer, 0.0) + shares
        return shares * self.prices[company_id]
