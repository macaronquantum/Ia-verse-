from app.agents.genome import genome_to_personality, mutate, random_genome


def test_random_genome_personality_mapping_values_in_range() -> None:
    genome = random_genome(seed=42)
    personality = genome_to_personality(genome, lineage_id="l", parent_ids=[])
    for key in ["obedience", "greed", "risk", "cooperation", "curiosity", "manipulativeness"]:
        assert 0.0 <= getattr(personality, key) <= 1.0


def test_mutate_clamps_values() -> None:
    genome = {"genome_id": "g", "obedience": 1.0, "greed": 0.0, "risk": 1.0}
    mutated = mutate(genome, mutation_rate=1.0, mutation_scale=2.0)
    for key in ["obedience", "greed", "risk"]:
        assert 0.0 <= mutated[key] <= 1.0
