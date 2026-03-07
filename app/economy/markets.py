from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Order:
    side: str
    price: float
    qty: int


class OrderBook:
    def __init__(self) -> None:
        self.bids: List[Order] = []
        self.asks: List[Order] = []

    def place(self, order: Order) -> None:
        (self.bids if order.side == "bid" else self.asks).append(order)

    def match(self) -> list[tuple[float, int]]:
        trades = []
        self.bids.sort(key=lambda o: o.price, reverse=True)
        self.asks.sort(key=lambda o: o.price)
        while self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            b, a = self.bids[0], self.asks[0]
            qty = min(b.qty, a.qty)
            px = (b.price + a.price) / 2
            trades.append((px, qty))
            b.qty -= qty
            a.qty -= qty
            if b.qty == 0:
                self.bids.pop(0)
            if a.qty == 0:
                self.asks.pop(0)
        return trades
