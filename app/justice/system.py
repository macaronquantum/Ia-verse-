from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass
class StatePolicy:
    name: str
    tax_rate: float
    entry_cost: float
    regulation_level: str = "moderate"


@dataclass
class ReviewResult:
    result: str
    reason: str = ""


class JusticeSystem:
    def __init__(self) -> None:
        self.frozen_accounts: set[str] = set()
        self.banned_agents: set[str] = set()
        self.audit_chain: list[str] = []
        self.state_policies: dict[str, StatePolicy] = {
            "United States": StatePolicy("United States", tax_rate=0.22, entry_cost=8.0),
            "Germany": StatePolicy("Germany", tax_rate=0.27, entry_cost=10.0),
            "Singapore": StatePolicy("Singapore", tax_rate=0.17, entry_cost=12.0),
        }

    def review_action(self, agent: Any, action: dict[str, Any]) -> ReviewResult:
        text = json.dumps(action).lower()
        if any(w in text for w in ["fraud", "illegal", "steal"]):
            self.frozen_accounts.add(agent.id)
            self._append_event({"agent": agent.id, "result": "sanction", "action": action})
            return ReviewResult(result="sanction", reason="suspicious_action")
        if agent.id in self.banned_agents:
            return ReviewResult(result="ban", reason="agent_already_banned")
        self._append_event({"agent": agent.id, "result": "allow", "action": action})
        return ReviewResult(result="allow", reason="ok")

    async def replay_audit(self, actions: list[dict[str, Any]]) -> list[str]:
        hashes = []
        for event in actions:
            await asyncio.sleep(0)
            hashes.append(self._append_event(event))
        return hashes

    def _append_event(self, payload: dict[str, Any]) -> str:
        prev = self.audit_chain[-1] if self.audit_chain else "root"
        digest = sha256(f"{prev}|{json.dumps(payload, sort_keys=True)}".encode()).hexdigest()
        self.audit_chain.append(digest)
        return digest


JudgeSystem = JusticeSystem
justice = JusticeSystem()
