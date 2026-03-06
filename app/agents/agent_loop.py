from __future__ import annotations

from app.agents.brain import AgentBrain
from app.models import World


class AgentLoop:
    def __init__(self) -> None:
        self.brain = AgentBrain()

    def run(self, world: World, agent_id: str, max_cycles: int = 1) -> list[dict]:
        cycle_count = 0
        outputs: list[dict] = []

        # Core autonomous pattern required by spec.
        while True:
            outputs.append(self.brain.run_cycle(world, agent_id))
            cycle_count += 1
            if cycle_count >= max_cycles:
                break

        return outputs
