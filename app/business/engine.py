"""Business lifecycle engine converting opportunities into provisioned startups."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agents.tool_factory import ToolFactory
from app.api_gateway.registry import ToolRegistry
from app.economy.opportunity_engine import Opportunity


@dataclass
class BusinessPlan:
    product_spec: str
    mvp_tasks: list[str]
    upfront_cost_estimate: float
    monthly_opex_estimate: float
    pricing_model: str
    customer_target: str
    marketing_plan: str
    compliance_risks: list[str]


class BusinessEngine:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or ToolRegistry()
        self.tool_factory = ToolFactory(self.registry)
        self.businesses: dict[str, dict] = {}

    def generate_plan(self, opportunity: Opportunity) -> BusinessPlan:
        return BusinessPlan(
            product_spec=opportunity.desc,
            mvp_tasks=["define api", "implement feature", "publish listing"],
            upfront_cost_estimate=opportunity.estimated_cost,
            monthly_opex_estimate=opportunity.estimated_cost * 0.2,
            pricing_model="subscription",
            customer_target="agents",
            marketing_plan="launch on marketplace and outbound to active companies",
            compliance_risks=["external-spend-review"],
        )

    def provision_business(self, agent_creator: str, plan: BusinessPlan) -> str:
        business_id = str(uuid4())
        build = self.tool_factory.build_and_publish(agent_creator, plan.product_spec[:40], price=19.0)
        self.businesses[business_id] = {"creator": agent_creator, "plan": plan, "tool_id": build.tool_id, "status": "active"}
        return business_id

    def scale_business(self, business_id: str) -> None:
        self.businesses[business_id]["status"] = "scaled"

    def liquidate_business(self, business_id: str) -> None:
        self.businesses[business_id]["status"] = "liquidated"
