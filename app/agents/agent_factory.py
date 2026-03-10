"""Sub-agent provisioning and lifecycle management with genome/personality support."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.agents import genome as genome_lib
from app.agents.evolution import spawn_child
from app.agents.personality import Personality
from app.config import COSTS, EVOLUTION
from app.memory.store import STORE


@dataclass
class WorkerAgent:
    id: str
    role: str
    salary: float
    skills: list[str] = field(default_factory=list)
    core_energy: float = 100.0
    personality: Personality | None = None


class AgentFactory:
    def __init__(self, seed: int | None = None) -> None:
        self.workers: dict[str, WorkerAgent] = {}
        self.seed = seed

    def create_sub_agent(self, creator_budget: float, role: str, template_skills: list[str]) -> tuple[WorkerAgent, float]:
        cost = COSTS.create_agent_costs[role]
        if creator_budget < cost:
            raise ValueError("insufficient CoreEnergy")
        genome = genome_lib.random_genome(seed=self.seed)
        personality = genome_lib.genome_to_personality(genome, lineage_id=str(uuid4()), parent_ids=[])
        worker = WorkerAgent(
            id=str(uuid4()),
            role=role,
            salary=cost * 0.2,
            skills=template_skills[:],
            core_energy=100.0,
            personality=personality,
        )
        STORE.save_personality(worker.id, personality.to_dict())
        STORE.register_lineage(personality.lineage_id, worker.id)
        self.workers[worker.id] = worker
        return worker, creator_budget - cost

    def create_child(self, creator_id: str, role: str, template_skills: list[str]) -> WorkerAgent:
        parent = self.workers.get(creator_id)
        if not parent:
            raise ValueError("creator not found")
        if parent.core_energy < EVOLUTION.spawn_energy_cost:
            raise ValueError("insufficient CoreEnergy")
        parent.core_energy -= EVOLUTION.spawn_energy_cost
        parent_genome = genome_lib.personality_to_genome(parent.personality) if parent.personality else genome_lib.random_genome()
        spec = spawn_child(
            parent_ids=[creator_id],
            energy_cost=EVOLUTION.spawn_energy_cost,
            mutation_rate=EVOLUTION.default_mutation_rate,
            seed=self.seed,
            parent_genomes=[parent_genome],
        )
        worker = WorkerAgent(
            id=spec.agent_id,
            role=role,
            salary=COSTS.create_agent_costs.get(role, 1.0) * 0.2,
            skills=template_skills[:],
            core_energy=50.0,
            personality=spec.personality,
        )
        self.workers[worker.id] = worker
        return worker

    def fire(self, worker_id: str) -> None:
        self.workers.pop(worker_id, None)


from dataclasses import field as _field

from app.agents.personality import Personality as _Personality


class CompanyTeam:
    def __init__(self, company_name: str) -> None:
        self.company_name = company_name
        self.members: list[WorkerAgent] = []

    def add(self, worker: WorkerAgent) -> None:
        self.members.append(worker)

    def payroll(self) -> float:
        return sum(w.salary for w in self.members)
