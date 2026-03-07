from statistics import mean, variance

from app.agents.evolution import spawn_child


def test_inheritance_mean_and_mutation_variance() -> None:
    p1 = {"genome_id": "a", "obedience": 0.2, "greed": 0.9, "risk": 0.4, "cooperation": 0.4, "curiosity": 0.2, "manipulativeness": 0.4, "ideology_idx": 0.0}
    p2 = {"genome_id": "b", "obedience": 0.8, "greed": 0.1, "risk": 0.6, "cooperation": 0.8, "curiosity": 0.4, "manipulativeness": 0.2, "ideology_idx": 1.0}
    vals = []
    for _ in range(100):
        spec = spawn_child(["p1", "p2"], energy_cost=10, mutation_rate=0.02, parent_genomes=[p1, p2])
        vals.append(spec.genome["obedience"])
    assert abs(mean(vals) - 0.5) < 0.1
    assert variance(vals) > 0.0
