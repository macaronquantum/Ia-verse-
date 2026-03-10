"""Sub-agent provisioning and lifecycle management with genome/personality support."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.agents import genome as genome_lib
from app.agents.evolution import spawn_child
from app.agents.personality import Personality
from app.config import COSTS, EVOLUTION
from app.memory.store import STORE


ROLE_ALIASES = {
    "dev": "worker",
    "citizen": "worker",
    "engineering": "worker",
    "operations": "worker",
}


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

    def _cost_for_role(self, role: str) -> float:
        return COSTS.create_agent_costs.get(role, COSTS.create_agent_costs.get(ROLE_ALIASES.get(role, "worker"), 1.0))

    def create_sub_agent(self, creator_budget: float, role: str, template_skills: list[str]) -> tuple[WorkerAgent, float]:
        cost = self._cost_for_role(role)
        if creator_budget < cost:
            raise ValueError("insufficient CoreEnergy")
        genome = genome_lib.random_genome(seed=self.seed)
        personality = genome_lib.genome_to_personality(genome, lineage_id=str(uuid4()), parent_ids=[])
        worker = WorkerAgent(
            id=str(uuid4()),
            role=role,
            salary=cost,
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
            salary=self._cost_for_role(role),
            skills=template_skills[:],
            core_energy=50.0,
            personality=spec.personality,
        )
        self.workers[worker.id] = worker
        return worker

    def spawn(self, team: "CompanyTeam", role: str, salary: float) -> WorkerAgent:
        worker = WorkerAgent(id=str(uuid4()), role=role, salary=salary, skills=team.parent_skills[:])
        team.members.append(worker)
        return worker

    def pay_salaries(self, team: "CompanyTeam") -> float:
        due = team.payroll()
        team.treasury -= due
        return due

    def fire(self, worker_id: str) -> None:
        self.workers.pop(worker_id, None)


class CompanyTeam:
    def __init__(self, company_name: str | None = None, treasury: float = 0.0, parent_skills: list[str] | None = None) -> None:
        self.company_name = company_name or "company"
        self.treasury = treasury
        self.parent_skills = parent_skills or []
        self.members: list[WorkerAgent] = []

    @property
    def agents(self) -> list[WorkerAgent]:
        return self.members

    def add(self, worker: WorkerAgent) -> None:
        self.members.append(worker)

    def payroll(self) -> float:
        return sum(w.salary for w in self.members)
