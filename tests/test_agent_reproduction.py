from app.agents.agent_factory import AgentFactory, CompanyTeam


def test_spawn_team_and_payroll() -> None:
    factory = AgentFactory()
    team = CompanyTeam(treasury=500, parent_skills=["product"])
    factory.spawn(team, "engineering", 50)
    factory.spawn(team, "operations", 40)
    paid = factory.pay_salaries(team)
    assert paid == 90
    assert team.treasury < 500
