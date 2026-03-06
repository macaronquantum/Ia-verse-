from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(slots=True)
class Order:
    agent_id: str
    market: str
    side: str
    quantity: float
    limit_price: float


@dataclass(slots=True)
class MarketBook:
    base_price: float = 10.0
    demand: float = 0.0
    supply: float = 0.0

    def price(self) -> float:
        imbalance = (self.demand - self.supply) / max(self.supply + self.demand, 1.0)
        return max(0.1, self.base_price * (1 + imbalance))


@dataclass
class MarketSystem:
    books: dict[str, MarketBook] = field(default_factory=lambda: defaultdict(MarketBook))
    traded_volume: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def submit_order(self, order: Order) -> None:
        book = self.books[order.market]
        if order.side == "buy":
            book.demand += order.quantity
        else:
            book.supply += order.quantity

    def tick(self) -> dict[str, float]:
        prices: dict[str, float] = {}
        for market_name, book in self.books.items():
            prices[market_name] = book.price()
            self.traded_volume[market_name] += min(book.demand, book.supply)
            book.base_price = prices[market_name]
            book.demand = 0.0
            book.supply = 0.0
        return prices

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {
            m: {"price": b.base_price, "demand": b.demand, "supply": b.supply, "volume": self.traded_volume[m]}
            for m, b in self.books.items()
        }
