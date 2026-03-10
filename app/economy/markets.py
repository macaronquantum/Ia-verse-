from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Order:
    agent_id: str
    market: str = "default"
    side: str = "buy"
    quantity: float = 1.0
    limit_price: float = 10.0
    price: float = 0.0
    order_type: str = "limit"

    def __post_init__(self) -> None:
        if self.price == 0.0 and self.limit_price > 0.0:
            self.price = self.limit_price


@dataclass
class Trade:
    buyer: str
    seller: str
    price: float
    quantity: float
    fee_paid: float


@dataclass
class OrderBook:
    symbol: str
    fee_rate: float = 0.001
    bids: List[Order] = field(default_factory=list)
    asks: List[Order] = field(default_factory=list)

    def place_order(self, order: Order) -> List[Trade]:
        if order.side == "buy":
            return self._match_buy(order)
        if order.side == "sell":
            return self._match_sell(order)
        raise ValueError("side must be buy/sell")

    def _match_buy(self, buy: Order) -> List[Trade]:
        trades: List[Trade] = []
        self.asks.sort(key=lambda o: o.price)
        remaining = buy.quantity
        while self.asks and remaining > 0:
            ask = self.asks[0]
            if buy.order_type == "limit" and buy.price < ask.price:
                break
            qty = min(remaining, ask.quantity)
            trade_price = ask.price
            fee = qty * trade_price * self.fee_rate
            trades.append(Trade(buyer=buy.agent_id, seller=ask.agent_id, price=trade_price, quantity=qty, fee_paid=fee))
            remaining -= qty
            ask.quantity -= qty
            if ask.quantity <= 0:
                self.asks.pop(0)
        if remaining > 0 and buy.order_type == "limit":
            buy.quantity = remaining
            self.bids.append(buy)
        return trades

    def _match_sell(self, sell: Order) -> List[Trade]:
        trades: List[Trade] = []
        self.bids.sort(key=lambda o: o.price, reverse=True)
        remaining = sell.quantity
        while self.bids and remaining > 0:
            bid = self.bids[0]
            if sell.order_type == "limit" and sell.price > bid.price:
                break
            qty = min(remaining, bid.quantity)
            trade_price = bid.price
            fee = qty * trade_price * self.fee_rate
            trades.append(Trade(buyer=bid.agent_id, seller=sell.agent_id, price=trade_price, quantity=qty, fee_paid=fee))
            remaining -= qty
            bid.quantity -= qty
            if bid.quantity <= 0:
                self.bids.pop(0)
        if remaining > 0 and sell.order_type == "limit":
            sell.quantity = remaining
            self.asks.append(sell)
        return trades


def estimate_slippage(book_depth: float, quantity: float) -> float:
    if book_depth <= 0:
        return 1.0
    return min(1.0, quantity / (book_depth * 10))


def amm_price(x_reserve: float, y_reserve: float, dx: float) -> float:
    if x_reserve <= 0 or y_reserve <= 0:
        raise ValueError("invalid reserves")
    k = x_reserve * y_reserve
    new_x = x_reserve + dx
    new_y = k / new_x
    return (y_reserve - new_y) / dx


class MarketSystem:
    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}
        self._pending: List[Order] = []

    def submit_order(self, order: Order) -> List[Trade]:
        market = order.market
        if market not in self._books:
            self._books[market] = OrderBook(symbol=market)
        return self._books[market].place_order(order)

    def tick(self) -> dict[str, float]:
        return {symbol: len(book.bids) + len(book.asks) for symbol, book in self._books.items()}
