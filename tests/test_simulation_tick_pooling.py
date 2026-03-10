import asyncio
from types import SimpleNamespace

from app.agents.worker_pool import AgentWorkerPool, InMemoryQueue
from app.simulation.init import TickOrchestrator


class DummyAgent:
    def __init__(self, idx):
        self.id = f"a{idx}"
        self.alive = True
        self.wallet = 100.0
        self.country = "United States"


def test_tick_publishes_jobs_to_pool():
    world = SimpleNamespace(id="w1", tick_count=1, energy_price=10.0, agents={f"a{i}": DummyAgent(i) for i in range(5)})
    pool = AgentWorkerPool(queue_backend=InMemoryQueue(), worker_count=1)
    orchestrator = TickOrchestrator(pool)

    async def run():
        count = await orchestrator.publish_tick(world)
        assert count > 0

    asyncio.run(run())
