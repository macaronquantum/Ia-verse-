from __future__ import annotations

from dataclasses import dataclass

from app.agents.agent_factory import AgentFactory, CompanyTeam
from app.agents.resource_optimizer import ResourceOptimizer


@dataclass
class BusinessPlan:
    name: str
    expected_return: float
    estimated_cost: float


class BusinessBuilder:
    def __init__(self) -> None:
        self.factory = AgentFactory()
        self.optimizer = ResourceOptimizer()

    def build(self, plan: BusinessPlan) -> CompanyTeam:
        decision = self.optimizer.choose_model(plan.estimated_cost, plan.expected_return)
        if decision["throttle"]:
            raise ValueError("plan throttled")
        team = CompanyTeam(treasury=plan.estimated_cost * 3, parent_skills=["ops", "build"])
        self.factory.spawn(team, "engineering", 20)
        return team
