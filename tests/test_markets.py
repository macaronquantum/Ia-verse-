from app.economy.markets import MarketSystem, Order


def test_supply_demand_price_movement():
    market = MarketSystem()
    market.submit_order(Order("a", "services", "buy", 10, 10))
    market.submit_order(Order("b", "services", "sell", 2, 10))
    prices = market.tick()
    assert prices["services"] > 10

    market.submit_order(Order("a", "services", "buy", 1, 10))
    market.submit_order(Order("b", "services", "sell", 10, 10))
    prices = market.tick()
    assert prices["services"] < 20
