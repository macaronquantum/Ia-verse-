from app.agents.agent_factory import AgentFactory
from app.agents.evolution import selection_step
from app.config import EVOLUTION
from app.memory.store import STORE


def test_seed_population_rebel_cap_and_fitness_signal() -> None:
    STORE.personalities.clear()
    STORE.fitness.clear()
    factory = AgentFactory(seed=7)
    for i in range(1000):
        worker, _ = factory.create_sub_agent(creator_budget=10_000.0, role="citizen", template_skills=["x"])
        STORE.fitness[worker.id] = {
            "survival_time": float(i % 10),
            "cumulative_energy_earned": worker.personality.greed * 10 if worker.personality else 0.0,
            "reputation": 0.0,
        }
    rebels = sum(1 for p in STORE.personalities.values() if p["type_tag"] == "rebel")
    assert rebels / len(STORE.personalities) <= EVOLUTION.max_rebel_fraction + 0.005
    culled = selection_step(list(STORE.personalities.keys()), selection_pressure=0.1)
    assert len(culled) == 100
