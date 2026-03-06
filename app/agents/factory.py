from __future__ import annotations

from app.agents.base import BaseAgent
from app.models import Action, AgentState, AgentTier


class BankAgent(BaseAgent):
    async def decide(self, context):
        actions = await super().decide(context)
        actions.append(
            Action(
                actor_id=self.state.agent_id,
                action_type="set_credit_offer",
                payload={"rate": context.interest_rates.get("USD", 0.02) + 0.01},
            )
        )
        return actions


class CentralBankAgent(BaseAgent):
    async def decide(self, context):
        actions = await super().decide(context)
        actions.append(
            Action(
                actor_id=self.state.agent_id,
                action_type="monetary_policy",
                payload={"currency": "USD", "rate_shift": -0.001},
            )
        )
        return actions


def build_agent(state: AgentState) -> BaseAgent:
    if state.tier == AgentTier.BANK:
        return BankAgent(state)
    if state.tier == AgentTier.CENTRAL_BANK:
        return CentralBankAgent(state)
    return BaseAgent(state)
