"""Sub-agent provisioning and lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.config import COSTS


@dataclass
class WorkerAgent:
    id: str
    role: str
    salary: float
    skills: list[str] = field(default_factory=list)


class AgentFactory:
    def __init__(self) -> None:
        self.workers: dict[str, WorkerAgent] = {}

    def create_sub_agent(self, creator_budget: float, role: str, template_skills: list[str]) -> tuple[WorkerAgent, float]:
        cost = COSTS.create_agent_costs[role]
        if creator_budget < cost:
            raise ValueError("insufficient CoreEnergy")
        worker = WorkerAgent(id=str(uuid4()), role=role, salary=cost * 0.2, skills=template_skills[:])
        self.workers[worker.id] = worker
        return worker, creator_budget - cost

    def fire(self, worker_id: str) -> None:
        self.workers.pop(worker_id, None)
