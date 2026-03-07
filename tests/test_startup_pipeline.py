from app.agents.business_builder import BusinessBuilder, BusinessPlan


def test_pipeline_builds_team_in_dev_mode() -> None:
    builder = BusinessBuilder()
    team = builder.build(BusinessPlan(name="Sensing SaaS", expected_return=500, estimated_cost=100))
    assert len(team.agents) >= 1
