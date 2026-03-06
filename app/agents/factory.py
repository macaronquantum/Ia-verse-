from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.base import (
    BankAgent,
    BaseAgent,
    CitizenAgent,
    CompanyAgent,
    JudgeAgent,
    OracleAgent,
)
from app.energy.core import EnergyLedger
from app.llm.adapters import HybridLLMAdapter


@dataclass
class AgentFactory:
    ledger: EnergyLedger
    llm: HybridLLMAdapter
    agents: dict[str, BaseAgent] = field(default_factory=dict)

    def create(self, kind: str, *, name: str, goals: list[str], skills: set[str], parent: BaseAgent | None = None) -> BaseAgent:
        cls_map = {
            "base": BaseAgent,
            "citizen": CitizenAgent,
            "company": CompanyAgent,
            "bank": BankAgent,
            "judge": JudgeAgent,
            "oracle": OracleAgent,
        }
        if kind not in cls_map:
            raise ValueError(f"Unknown agent type: {kind}")

        if parent:
            self.ledger.charge_creation(parent.agent_id)
            inherited = set(list(parent.skills)[: max(1, len(parent.skills) // 2)])
            skills = skills | inherited

        agent = cls_map[kind](name=name, skills=skills, goals=goals, ledger=self.ledger, llm=self.llm, parent_id=parent.agent_id if parent else None)
        self.agents[agent.agent_id] = agent
        if self.ledger.balance_of(agent.agent_id) == 0:
            self.ledger.mint(agent.agent_id, 20.0)
        return agent
