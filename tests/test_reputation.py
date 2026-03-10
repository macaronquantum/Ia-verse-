from app.economy.reputation import ReputationEngine


def test_reputation_moves_with_transactions_judgments_and_contributions() -> None:
    eng = ReputationEngine()
    start = eng.ensure("a1").score
    up = eng.record_transaction("a1", success=True)
    assert up > start
    down = eng.record_transaction("a1", success=False)
    assert down < up
    after_judge = eng.record_judgment("a1", severe=True)
    assert after_judge < down
    recovered = eng.record_economic_contribution("a1", 5000)
    assert recovered > after_judge


def test_reputation_influences_credit_and_price_impact() -> None:
    eng = ReputationEngine()
    eng.ensure("bank")
    eng.apply_transparency_adjustment("bank", 0.95)
    eng.record_economic_contribution("bank", 50_000)
    for _ in range(20):
        eng.record_transaction("bank", success=True)
    assert eng.counterparty_credit_limit_multiplier("bank") >= 1.3
    assert eng.price_impact_multiplier("bank") < 0.8
