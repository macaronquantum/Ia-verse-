from app.economy.market_analyzer import detect_arbitrage


def test_detect_arbitrage_from_orderbook() -> None:
    alerts = detect_arbitrage({"TOOL": {"bid": 10, "ask": 12.5, "external_price": 15}}, threshold=1.0)
    assert any("buy local" in a for a in alerts)
