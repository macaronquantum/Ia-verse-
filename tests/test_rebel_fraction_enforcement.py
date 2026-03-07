from app.agents.evolution import spawn_child
from app.config import EVOLUTION
from app.memory.store import STORE


def test_rebel_fraction_cap() -> None:
    STORE.personalities.clear()
    old = EVOLUTION.max_rebel_fraction
    EVOLUTION.max_rebel_fraction = 0.01
    rebel_genome = {
        "genome_id": "r",
        "obedience": 0.1,
        "greed": 0.7,
        "risk": 0.8,
        "cooperation": 0.2,
        "curiosity": 0.4,
        "manipulativeness": 0.9,
        "ideology_idx": 0.5,
    }
    for i in range(1000):
        spawn_child([f"p{i}"], energy_cost=10, mutation_rate=0.0, parent_genomes=[rebel_genome])
    rebels = sum(1 for p in STORE.personalities.values() if p["type_tag"] == "rebel")
    assert rebels / len(STORE.personalities) <= 0.01
    EVOLUTION.max_rebel_fraction = old
