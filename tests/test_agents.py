import asyncio

from app.agents.factory import AgentFactory
from app.api_gateway.gateway import APIGateway
from app.energy.core import EnergyLedger
from app.llm.adapters import HybridLLMAdapter


def test_agent_creation_and_inherited_skills():
    async def scenario() -> None:
        ledger = EnergyLedger()
        llm = HybridLLMAdapter(APIGateway())
        factory = AgentFactory(ledger, llm)

        parent = factory.create("company", name="ParentCo", goals=["grow"], skills={"trade", "build", "hire"})
        pre_balance = ledger.balance_of(parent.agent_id)
        child = factory.create("citizen", name="Child", goals=["work"], skills={"learn"}, parent=parent)

        assert ledger.balance_of(parent.agent_id) == pre_balance - ledger.config.agent_creation_cost
        assert child.parent_id == parent.agent_id
        assert "learn" in child.skills
        assert len(child.skills) >= 2

    asyncio.run(scenario())
