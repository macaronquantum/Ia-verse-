from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(init=False)
class Order:
    agent_id: str
    market: str = "default"
    side: str = "buy"
    quantity: float = 1.0
    limit_price: float = 10.0
    price: float = 0.0
    order_type: str = "limit"

    def __init__(self, *args, **kwargs) -> None:
        # Backward-compatible constructor forms:
        # 1) Order(agent_id, market, side, quantity, limit_price)
        # 2) Order(side, price, quantity) for legacy orderbook tests
        if len(args) == 3 and not kwargs and args[0] in {"bid", "ask", "buy", "sell"}:
            side = "buy" if args[0] in {"bid", "buy"} else "sell"
            self.agent_id = str(args[0])
            self.market = "default"
            self.side = side
            self.quantity = float(args[2])
            self.limit_price = float(args[1])
            self.price = float(args[1])
            self.order_type = "limit"
            return

        self.agent_id = kwargs.pop("agent_id", args[0] if len(args) > 0 else "")
        self.market = kwargs.pop("market", args[1] if len(args) > 1 else "default")
        self.side = kwargs.pop("side", args[2] if len(args) > 2 else "buy")
        self.quantity = float(kwargs.pop("quantity", args[3] if len(args) > 3 else 1.0))
        self.limit_price = float(kwargs.pop("limit_price", kwargs.pop("price", args[4] if len(args) > 4 else 10.0)))
        self.price = float(kwargs.pop("price", self.limit_price))
        self.order_type = kwargs.pop("order_type", "limit")
        if kwargs:
            raise TypeError(f"unexpected keyword arguments: {','.join(kwargs.keys())}")


@dataclass
class Trade:
    buyer: str
    seller: str
    price: float
    quantity: float
    fee_paid: float


@dataclass
class OrderBook:
    symbol: str = "default"
    fee_rate: float = 0.001
    bids: List[Order] = field(default_factory=list)
    asks: List[Order] = field(default_factory=list)

    def place_order(self, order: Order) -> List[Trade]:
        if order.side == "buy":
            return self._match_buy(order)
        if order.side == "sell":
            return self._match_sell(order)
        raise ValueError("side must be buy/sell")

    def place(self, order: Order) -> List[Trade]:
        if order.side == "buy":
            self.bids.append(order)
        elif order.side == "sell":
            self.asks.append(order)
        else:
            raise ValueError("side must be buy/sell")
        return []

    def match(self) -> list[tuple[float, float]]:
        trades: list[tuple[float, float]] = []
        self.bids.sort(key=lambda o: o.price, reverse=True)
        self.asks.sort(key=lambda o: o.price)
        while self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            bid = self.bids[0]
            ask = self.asks[0]
            qty = min(bid.quantity, ask.quantity)
            price = (bid.price + ask.price) / 2
            trades.append((price, qty))
            bid.quantity -= qty
            ask.quantity -= qty
            if bid.quantity <= 0:
                self.bids.pop(0)
            if ask.quantity <= 0:
                self.asks.pop(0)
        return trades

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

    def submit_order(self, order: Order) -> List[Trade]:
        market = order.market
        if market not in self._books:
            self._books[market] = OrderBook(symbol=market)
        return self._books[market].place_order(order)

    def tick(self) -> dict[str, float]:
        prices: dict[str, float] = {}
        for symbol, book in self._books.items():
            buy_qty = sum(o.quantity for o in book.bids)
            sell_qty = sum(o.quantity for o in book.asks)
            imbalance = buy_qty - sell_qty
            base = 10.0
            prices[symbol] = max(0.1, base + imbalance)
        return prices
