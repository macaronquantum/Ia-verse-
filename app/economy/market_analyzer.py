"""Market signal and arbitrage detector."""

from __future__ import annotations


def compute_spread(bid: float, ask: float) -> float:
    return max(ask - bid, 0.0)


def detect_arbitrage(orderbooks: dict[str, dict[str, float]], threshold: float = 1.0) -> list[str]:
    alerts: list[str] = []
    for symbol, book in orderbooks.items():
        spread = compute_spread(book["bid"], book["ask"])
        if spread > threshold:
            alerts.append(f"{symbol}: wide spread {spread:.2f}")
        if book.get("external_price", book["ask"]) > book["ask"] + threshold:
            alerts.append(f"{symbol}: buy local / sell external")
    return alerts
