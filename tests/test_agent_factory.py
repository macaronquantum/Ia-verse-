from app.agents.agent_factory import AgentFactory


def test_create_dev_and_workers_budget_and_skills() -> None:
    factory = AgentFactory()
    budget = 20.0
    dev, budget = factory.create_sub_agent(budget, "dev", ["python"])
    assert dev.skills == ["python"]
    for _ in range(3):
        _, budget = factory.create_sub_agent(budget, "citizen", ["execution"])
    assert budget < 20.0
