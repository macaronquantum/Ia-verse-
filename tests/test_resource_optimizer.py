from app.agents.resource_optimizer import ResourceOptimizer


def test_resource_optimizer_throttles_negative_margin() -> None:
    opt = ResourceOptimizer()
    decision = opt.choose_model(estimated_cost=100, expected_return=20)
    assert decision["throttle"] is True
