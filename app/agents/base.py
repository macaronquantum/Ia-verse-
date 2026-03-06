from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from app.models import Action, AgentState


@dataclass
class AgentContext:
    tick_id: int
    interest_rates: dict[str, float]


class BaseAgent:
    """Autonomous economic actor with minimal strategy hooks."""

    def __init__(self, state: AgentState):
        self.state = state

    async def observe(self, context: AgentContext) -> None:
        self.state.memory.history.append(f"Observed tick {context.tick_id}")

    async def decide(self, context: AgentContext) -> List[Action]:
        if not self.state.alive:
            return []

        actions: List[Action] = []
        if self.state.tier.value.startswith("tier1") and random.random() < 0.7:
            actions.append(
                Action(
                    actor_id=self.state.agent_id,
                    action_type="produce_value",
                    payload={"value": random.uniform(0.5, 2.0), "currency": "USD"},
                )
            )
        elif self.state.tier.value.startswith("tier2") and random.random() < 0.5:
            actions.append(
                Action(
                    actor_id=self.state.agent_id,
                    action_type="trade",
                    payload={"sell": "USD", "buy": "EUR", "amount": random.uniform(0.2, 1.5)},
                )
            )

        return actions
