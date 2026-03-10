from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from uuid import uuid4

from app.models import AgentBusiness, World


@dataclass
class BusinessPlan:
    name: str = ""
    industry: str = ""
    target_revenue: float = 0.0
    expected_return: float = 0.0
    estimated_cost: float = 0.0
    steps: list[str] = field(default_factory=list)


@dataclass
class SaleSettlement:
    creator_share: float
    platform_fee: float


class BusinessBuilder:
    DEFAULT_BUSINESSES = [
        ("automation services", "workflow automation API"),
        ("data APIs", "market signals API"),
        ("content engines", "autonomous content feed"),
        ("design generators", "design generation studio"),
        ("market analytics tools", "analytics dashboard service"),
    ]

    def create_business(self, world: World, agent_id: str, kind: str | None = None) -> AgentBusiness:
        selected = self.DEFAULT_BUSINESSES[0]
        if kind:
            for item in self.DEFAULT_BUSINESSES:
                if item[0] == kind:
                    selected = item
                    break

        business = AgentBusiness(
            id=str(uuid4()),
            owner_agent_id=agent_id,
            name=f"{selected[0]} by {agent_id[:6]}",
            product=selected[1],
            price=25.0,
            cost=7.5,
            revenue_streams=["subscriptions", "api_usage", "licensing"],
            target_users=["agents", "humans"],
        )
        world.businesses[business.id] = business
        world.agents_table[agent_id]["businesses"].append(business.id)
        return business

    def create_listing(self, tool_id: str, model: str) -> dict:
        return {"tool_id": tool_id, "pricing_model": model, "status": "listed"}

    def settle_sale(self, amount: float) -> SaleSettlement:
        fee = amount * 0.1
        return SaleSettlement(creator_share=amount - fee, platform_fee=fee)

    def build(self, plan: BusinessPlan):
        agents = ["builder-1", "operator-1"] if (plan.expected_return or plan.target_revenue) > 0 else ["builder-1"]
        return SimpleNamespace(name=plan.name or "startup-team", agents=agents)
