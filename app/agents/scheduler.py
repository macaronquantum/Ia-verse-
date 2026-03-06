from __future__ import annotations

from app.agents.agent_loop import AgentLoop
from app.models import World


class AutonomousScheduler:
    """Distributed-scheduler placeholder (Redis/Celery compatible interface)."""

    def __init__(self) -> None:
        self.loop = AgentLoop()

    def run_background_cycle(self, world: World, cycles_per_agent: int = 1) -> dict:
        results: dict[str, list[dict]] = {}
        for agent_id in world.agents_table:
            results[agent_id] = self.loop.run(world, agent_id, max_cycles=cycles_per_agent)
        return results
