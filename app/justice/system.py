from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
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

    @property
    def allowed(self) -> bool:
        return self.result == "allow"


@dataclass
class HireReview:
    approved: bool
    reason: str = ""


class JusticeSystem:
    def __init__(self, _ledger: Any | None = None, auto_block_threshold: int = 3) -> None:
        self.frozen_accounts: set[str] = set()
        self.banned_agents: set[str] = set()
        self.audit_chain: list[str] = []
        self.state_policies: dict[str, StatePolicy] = {
            "United States": StatePolicy("United States", tax_rate=0.22, entry_cost=8.0),
            "Germany": StatePolicy("Germany", tax_rate=0.27, entry_cost=10.0),
            "Singapore": StatePolicy("Singapore", tax_rate=0.17, entry_cost=12.0),
        }
        self.main_judge_id: str | None = None
        self.auto_block_threshold = auto_block_threshold
        self._violations: dict[str, int] = {}

    def _agent_id(self, agent: Any) -> str:
        return getattr(agent, "id", agent)

    def review_action(self, agent: Any, action: Any, amount: float | None = None) -> ReviewResult:
        agent_id = self._agent_id(agent)
        action_payload = action if isinstance(action, dict) else {"action": str(action), "amount": amount}
        text = json.dumps(action_payload).lower()
        if any(w in text for w in ["fraud", "illegal", "steal"]):
            self._violations[agent_id] = self._violations.get(agent_id, 0) + 1
            self.frozen_accounts.add(agent_id)
            if self._violations[agent_id] >= self.auto_block_threshold:
                self.banned_agents.add(agent_id)
            self._append_event({"agent": agent_id, "result": "sanction", "action": action_payload})
            return ReviewResult(result="sanction", reason="suspicious_action")
        if agent_id in self.banned_agents:
            return ReviewResult(result="ban", reason="agent_already_banned")
        self._append_event({"agent": agent_id, "result": "allow", "action": action_payload})
        return ReviewResult(result="allow", reason="ok")

    def review_hire(self, budget: float, risky: bool = False) -> HireReview:
        if risky:
            return HireReview(False, "risky_hire")
        if budget >= 1000:
            return HireReview(False, "manual_review_required")
        return HireReview(True, "ok")

    def bootstrap_main_judge(self, judge_id: str) -> None:
        if self.main_judge_id and self.main_judge_id != judge_id:
            raise ValueError("principal judge already exists")
        self.main_judge_id = judge_id

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
