from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.energy.core import EnergyLedger
from app.llm.adapters import HybridLLMAdapter
from app.memory.store import AgentMemory


@dataclass(slots=True)
class Action:
    actor_id: str
    kind: str
    payload: dict[str, Any]
    cost: float = 0.0


@dataclass(slots=True)
class BaseAgent:
    name: str
    skills: set[str]
    goals: list[str]
    ledger: EnergyLedger
    llm: HybridLLMAdapter
    parent_id: str | None = None
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory: AgentMemory = field(default_factory=AgentMemory)

    async def perceive(self, environment: dict[str, Any]) -> dict[str, Any]:
        perception = {
            "goals": self.goals,
            "energy": self.ledger.balance_of(self.agent_id),
            "market": environment.get("market_snapshot", {}),
        }
        self.memory.add_short_term("perception", perception)
        return perception

    async def reason(self, perception: dict[str, Any]) -> dict[str, Any]:
        prompt = f"Agent {self.name} goals={self.goals} perception={perception}"
        response, used_external = await self.llm.complete(prompt, depth=perception["energy"] / 100.0)
        self.ledger.charge_reasoning(self.agent_id, external=used_external)
        thought = {"text": response, "used_external": used_external}
        self.memory.add_short_term("reasoning", thought)
        return thought

    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        action = Action(self.agent_id, "trade", {"intent": "market_scan"}, cost=self.ledger.config.base_action_cost)
        return [action]

    async def on_tick(self, environment: dict[str, Any]) -> list[Action]:
        self.ledger.charge_maintenance(self.agent_id)
        perception = await self.perceive(environment)
        thought = await self.reason(perception)
        actions = await self.decide_actions(thought)
        return actions


@dataclass(slots=True)
class CitizenAgent(BaseAgent):
    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        return [Action(self.agent_id, "offer_labor", {"hours": 1}, cost=0.5)]


@dataclass(slots=True)
class CompanyAgent(BaseAgent):
    employees: set[str] = field(default_factory=set)

    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        return [
            Action(self.agent_id, "produce", {"product": "digital_service", "qty": 1}, cost=1.0),
            Action(self.agent_id, "trade", {"market": "services", "side": "sell", "qty": 1}, cost=0.8),
        ]


@dataclass(slots=True)
class BankAgent(BaseAgent):
    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        return [Action(self.agent_id, "allocate_capital", {"budget": 5.0}, cost=1.2)]


@dataclass(slots=True)
class JudgeAgent(BaseAgent):
    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        return [Action(self.agent_id, "audit", {"scope": "market"}, cost=0.7)]


@dataclass(slots=True)
class OracleAgent(BaseAgent):
    async def decide_actions(self, thought: dict[str, Any]) -> list[Action]:
        return [Action(self.agent_id, "api_fetch", {"source": "macro_feed"}, cost=1.0)]
