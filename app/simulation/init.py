from __future__ import annotations

import random
from typing import Any

from app.agents.worker_pool import AgentJob, AgentWorkerPool
from app.config import settings
from app.justice.system import JusticeSystem, ReviewResult


class TickOrchestrator:
    def __init__(self, worker_pool: AgentWorkerPool, justice: JusticeSystem | None = None) -> None:
        self.worker_pool = worker_pool
        self.justice = justice or JusticeSystem()

    async def publish_tick(self, world: Any) -> int:
        active = [a for a in world.agents.values() if a.alive]
        sample_size = min(settings.ACTIVE_AGENTS_PER_TICK, len(active))
        chosen = random.sample(active, sample_size) if sample_size < len(active) else active
        for agent in chosen:
            await self.worker_pool.enqueue(
                AgentJob(
                    agent_id=agent.id,
                    world_id=world.id,
                    agent_state={"id": agent.id, "wallet": agent.wallet, "country": agent.country},
                    world_state={"tick": world.tick_count, "energy_price": world.energy_price},
                    metadata={"intent": "tick_decision"},
                )
            )
        return len(chosen)

    def apply_action_with_justice(self, agent: Any, action: dict[str, Any]) -> ReviewResult:
        review = self.justice.review_action(agent, action)
        if review.result == "sanction":
            agent.wallet = max(0.0, agent.wallet - 5.0)
        elif review.result == "ban":
            agent.alive = False
        if action.get("action") == "change_state":
            target = action.get("target_state")
            state = self.justice.state_policies.get(target)
            if state and agent.wallet >= state.entry_cost:
                agent.wallet -= state.entry_cost
                agent.country = target
        return review
