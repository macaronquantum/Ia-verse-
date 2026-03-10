"""Evolutionary operations: spawning, imitation and selection."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any
from uuid import uuid4

from app.agents import genome as genome_lib
from app.agents.personality import Personality
from app.config import EVOLUTION
from app.memory.store import STORE


@dataclass
class AgentSpec:
    agent_id: str
    genome: dict[str, Any]
    personality: Personality


def _rebel_fraction() -> float:
    total = len(STORE.personalities)
    if total == 0:
        return 0.0
    rebels = sum(1 for p in STORE.personalities.values() if p.get("type_tag") == "rebel")
    return rebels / total


def spawn_child(
    parent_ids: list[str],
    energy_cost: float,
    mutation_rate: float | None,
    seed: int | None = None,
    parent_genomes: list[dict[str, Any]] | None = None,
) -> AgentSpec:
    if energy_cost <= 0:
        raise ValueError("energy cost must be positive")
    rng = random.Random(seed)
    if not parent_genomes:
        child_genome = genome_lib.random_genome(seed=seed)
        lineage_id = str(uuid4())
    else:
        lineage_id = STORE.personalities.get(parent_ids[0], {}).get("lineage_id", str(uuid4())) if parent_ids else str(uuid4())
        if len(parent_genomes) == 1:
            child_genome = dict(parent_genomes[0])
            child_genome["genome_id"] = str(uuid4())
        else:
            method = "uniform" if EVOLUTION.child_inheritance != "average" else "single_point"
            child_genome = genome_lib.crossover(parent_genomes[0], parent_genomes[1], method=method)
            if EVOLUTION.child_inheritance == "average":
                for key in ["obedience", "greed", "risk", "cooperation", "curiosity", "manipulativeness"]:
                    base = (float(parent_genomes[0][key]) + float(parent_genomes[1][key])) / 2
                    child_genome[key] = max(0.0, min(1.0, base + random.gauss(0.0, 1e-4)))
        child_genome = genome_lib.mutate(
            child_genome,
            mutation_rate=mutation_rate if mutation_rate is not None else EVOLUTION.default_mutation_rate,
            mutation_scale=EVOLUTION.default_mutation_scale,
        )
    personality = genome_lib.genome_to_personality(child_genome, lineage_id=lineage_id, parent_ids=parent_ids)
    if personality.type_tag == "rebel" and _rebel_fraction() >= EVOLUTION.max_rebel_fraction:
        personality.type_tag = "opportunist"
    agent_id = str(uuid4())
    STORE.save_personality(agent_id, personality.to_dict())
    STORE.register_lineage(personality.lineage_id, agent_id)
    STORE.log_tamper_event({"kind": "spawn", "agent_id": agent_id, "parent_ids": parent_ids, "energy_cost": energy_cost})
    return AgentSpec(agent_id=agent_id, genome=child_genome, personality=personality)


def imitation_event(observer_id: str, model_id: str, trait_list: list[str], prob: float) -> bool:
    observer = STORE.personalities.get(observer_id)
    model = STORE.personalities.get(model_id)
    if not observer or not model:
        return False
    success = STORE.fitness.get(model_id, {}).get("fitness", 0.0)
    curiosity = float(observer.get("curiosity", 0.0))
    p = min(1.0, prob * (1 + curiosity) * (1 + max(0.0, success)))
    if random.random() > p:
        return False
    for trait in trait_list:
        if trait in observer and trait in model:
            observer[trait] = max(0.0, min(1.0, float(model[trait]) + random.gauss(0.0, EVOLUTION.default_mutation_scale / 2)))
    STORE.personalities[observer_id] = observer
    STORE.memetic_spread_count += 1
    STORE.log_tamper_event({"kind": "imitation", "observer_id": observer_id, "model_id": model_id, "traits": trait_list})
    return True


def selection_step(population: list[str], selection_pressure: float) -> list[str]:
    scored: list[tuple[str, float]] = []
    for agent_id in population:
        f = STORE.fitness.get(agent_id, {})
        score = 0.6 * f.get("cumulative_energy_earned", 0.0) + 0.4 * f.get("survival_time", 0.0)
        scored.append((agent_id, score))
        STORE.fitness.setdefault(agent_id, {})["fitness"] = score
    scored.sort(key=lambda x: x[1])
    k = int(len(scored) * selection_pressure)
    return [agent_id for agent_id, _ in scored[:k]]
