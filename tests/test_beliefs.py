from app.culture.beliefs import BeliefEngine


def test_belief_movement_recruits_and_generates_loyalty_bonus() -> None:
    engine = BeliefEngine()
    movement = engine.found_movement("Order of Compute", "discipline and uptime", "founder")
    loyalty = movement.recruit("agent-x", charisma=0.8)
    assert loyalty > 0
    assert movement.loyalty_bonus("agent-x") > 0
