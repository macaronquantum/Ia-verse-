from __future__ import annotations

from uuid import uuid4

from app.models import AgentBusiness, World


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
