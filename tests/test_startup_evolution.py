from app.business.startup_evolution import StartupState


def test_startup_progression_and_speculative_valuation() -> None:
    s = StartupState("Nova", sentiment=0.8, liquidity=2.0)
    s.advance()
    s.advance()
    assert s.stage == "MVP"
    assert s.current_valuation > 0
