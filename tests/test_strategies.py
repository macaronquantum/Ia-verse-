from app.agents.strategies import Strategy, StrategyContext, StrategyManager


def test_survival_is_primary_when_energy_low() -> None:
    mgr = StrategyManager()
    ctx = StrategyContext(
        energy_balance=5,
        profitability=1.0,
        risk_tolerance=1.0,
        reputation_score=1.0,
        market_volatility=1.0,
        liquidity=1.0,
    )
    assert mgr.choose_strategy(ctx) == Strategy.SURVIVAL_BASIC


def test_explorer_selected_for_high_curiosity_and_energy() -> None:
    mgr = StrategyManager()
    ctx = StrategyContext(
        energy_balance=80,
        profitability=0.2,
        risk_tolerance=0.3,
        reputation_score=0.8,
        market_volatility=0.2,
        liquidity=0.4,
        curiosity=0.95,
    )
    assert mgr.choose_strategy(ctx) == Strategy.EXPLORER
    assert Strategy.EXPLORER in mgr.strategy_history


def test_strategy_catalog_contains_full_requested_examples() -> None:
    catalog = StrategyManager.available_strategies()
    assert len(catalog) >= 15
    assert "religious_movement_founder" in catalog
