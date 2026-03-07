from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SubAgent:
    role: str
    salary: float
    retained: bool = True


@dataclass
class CompanyTeam:
    treasury: float
    parent_skills: List[str]
    agents: List[SubAgent] = field(default_factory=list)


class AgentFactory:
    def spawn(self, team: CompanyTeam, role: str, salary: float) -> SubAgent:
        if team.treasury < salary:
            raise ValueError("insufficient treasury")
        team.treasury -= salary * 0.1
        sub = SubAgent(role=role, salary=salary)
        team.agents.append(sub)
        return sub

    def pay_salaries(self, team: CompanyTeam) -> float:
        total = sum(a.salary for a in team.agents if a.retained)
        if total > team.treasury:
            for a in team.agents:
                a.retained = False
            return 0.0
        team.treasury -= total
        return total
