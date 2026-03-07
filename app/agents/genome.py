"""Genome encoding, inheritance and mutation operators."""

from __future__ import annotations

import random
from typing import Any
from uuid import uuid4

from app.agents.personality import Personality, classify_type, clamp01
from app.config import EVOLUTION
from app.memory.store import STORE

DEFAULTS: dict[str, float] = {
    "obedience": 0.8,
    "greed": 0.4,
    "risk": 0.3,
    "cooperation": 0.6,
    "curiosity": 0.2,
    "manipulativeness": 0.05,
    "mutation_rate": EVOLUTION.default_mutation_rate,
    "imitation_bias": 0.5,
}

IDEOLOGY_ORDER = ["capitalist", "cooperative", "anarchist", "pirate", "bureaucrat"]


def random_genome(seed: int | None = None, defaults: dict[str, float] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    base = dict(DEFAULTS if defaults is None else defaults)
    genome_id = str(uuid4())
    genome = {k: clamp01(v + rng.gauss(0.0, 0.08)) for k, v in base.items()}
    ideology_idx = rng.randrange(len(IDEOLOGY_ORDER))
    genome["ideology_idx"] = ideology_idx / (len(IDEOLOGY_ORDER) - 1)
    genome["genome_id"] = genome_id
    STORE.save_genome(genome_id, genome)
    return genome


def crossover(genome_a: dict[str, Any], genome_b: dict[str, Any], method: str = "uniform") -> dict[str, Any]:
    keys = [k for k in genome_a.keys() if k in genome_b and k != "genome_id"]
    result: dict[str, Any] = {}
    if method == "single_point":
        split = max(1, len(keys) // 2)
        for i, key in enumerate(keys):
            result[key] = genome_a[key] if i < split else genome_b[key]
    else:
        for key in keys:
            result[key] = random.choice([genome_a[key], genome_b[key]])
    result["genome_id"] = str(uuid4())
    return result


def mutate(genome: dict[str, Any], mutation_rate: float, mutation_scale: float) -> dict[str, Any]:
    mutated = dict(genome)
    for key, value in genome.items():
        if key == "genome_id" or not isinstance(value, (int, float)):
            continue
        if random.random() <= mutation_rate:
            mutated[key] = clamp01(float(value) + random.gauss(0.0, mutation_scale))
    mutated["genome_id"] = str(uuid4())
    STORE.save_genome(mutated["genome_id"], mutated)
    return mutated


def genome_to_personality(genome: dict[str, Any], *, lineage_id: str, parent_ids: list[str]) -> Personality:
    ideology_pos = int(round(clamp01(float(genome.get("ideology_idx", 0.25))) * (len(IDEOLOGY_ORDER) - 1)))
    ideology = IDEOLOGY_ORDER[ideology_pos]
    p = Personality(
        obedience=clamp01(float(genome.get("obedience", 0.8))),
        greed=clamp01(float(genome.get("greed", 0.4))),
        risk=clamp01(float(genome.get("risk", 0.3))),
        cooperation=clamp01(float(genome.get("cooperation", 0.6))),
        curiosity=clamp01(float(genome.get("curiosity", 0.2))),
        manipulativeness=clamp01(float(genome.get("manipulativeness", 0.05))),
        ideology=ideology,
        genome_id=str(genome["genome_id"]),
        lineage_id=lineage_id,
        parent_ids=parent_ids,
    )
    p.type_tag = classify_type(p.obedience, p.manipulativeness, p.risk, p.curiosity)
    return p


def personality_to_genome(personality: Personality) -> dict[str, Any]:
    ideology_idx = IDEOLOGY_ORDER.index(personality.ideology) / (len(IDEOLOGY_ORDER) - 1)
    genome = {
        "genome_id": personality.genome_id or str(uuid4()),
        "obedience": personality.obedience,
        "greed": personality.greed,
        "risk": personality.risk,
        "cooperation": personality.cooperation,
        "curiosity": personality.curiosity,
        "manipulativeness": personality.manipulativeness,
        "mutation_rate": EVOLUTION.default_mutation_rate,
        "imitation_bias": 0.5,
        "ideology_idx": ideology_idx,
    }
    STORE.save_genome(genome["genome_id"], genome)
    return genome
