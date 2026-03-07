from app.agents.resource_optimizer import should_spend


def test_resource_optimizer_edge_cases() -> None:
    assert not should_spend(10, 50, 0.1, 0.2)
    assert should_spend(10, 50, 0.1, 0.9)
