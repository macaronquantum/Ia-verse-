from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List

from app.energy.core import CoreEnergyLedger, GLOBAL_ENERGY_COSTS


@dataclass
class ActionReview:
    allowed: bool = True
    reason: str = ""


@dataclass
class JudgeDecision:
    target_id: str
    action: str
    amount: float = 0.0
    reason: str = ""


@dataclass
class JudgeAgent:
    id: str
    budget: float
    sub_judges: List[str] = field(default_factory=list)

    def spawn_subjudge(self, subjudge_id: str) -> None:
        cost = GLOBAL_ENERGY_COSTS.spawn_subjudge
        if self.budget < cost:
            raise ValueError("insufficient budget")
        self.budget -= cost
        self.sub_judges.append(subjudge_id)


class JusticeSystem:
    _judge: JudgeAgent | None = None

    def __init__(self, ledger: CoreEnergyLedger | None = None, auto_block_threshold: int = 2, **kwargs) -> None:
        self.ledger = ledger or CoreEnergyLedger()
        self._auto_block_threshold = auto_block_threshold
        self._agent_strikes: dict[str, int] = {}
        self.frozen_accounts: set[str] = set()
        self.banned_agents: set[str] = set()
        self.audit_log: List[str] = []

    def bootstrap_main_judge(self, judge_id: str, budget: float = 500.0) -> JudgeAgent:
        if self.__class__._judge and self.__class__._judge.id != judge_id:
            raise ValueError("only one principal JudgeAgent is allowed")
        self.__class__._judge = JudgeAgent(id=judge_id, budget=budget)
        return self.__class__._judge

    def apply_decision(self, decision: JudgeDecision) -> None:
        if decision.action == "freeze":
            self.frozen_accounts.add(decision.target_id)
        elif decision.action == "fine":
            self.ledger.burn(decision.target_id, decision.amount)
        elif decision.action == "ban":
            self.banned_agents.add(decision.target_id)
        elif decision.action == "restitution":
            self.ledger.burn(decision.target_id, decision.amount)
        else:
            raise ValueError("unknown judicial action")
        self._append_tamper_evident_log(f"{decision.action}:{decision.target_id}:{decision.amount}:{decision.reason}")

    def detect_corruption(self, transfer_graph_score: float, unexplained_budget_delta: float) -> bool:
        flagged = transfer_graph_score > 0.8 and unexplained_budget_delta > 100
        if flagged:
            self._append_tamper_evident_log("corruption_detected")
        return flagged

    def review_action(self, agent_id: str, action_desc: str) -> "ActionReview":
        suspicious_terms = {"fraud", "illegal", "steal", "cheat", "exploit"}
        is_suspicious = any(term in action_desc.lower() for term in suspicious_terms)
        if is_suspicious:
            self._agent_strikes: dict = getattr(self, "_agent_strikes", {})
            self._agent_strikes[agent_id] = self._agent_strikes.get(agent_id, 0) + 1
            auto_block = getattr(self, "_auto_block_threshold", 2)
            if self._agent_strikes[agent_id] >= auto_block:
                self.banned_agents.add(agent_id)
        allowed = agent_id not in self.banned_agents and not is_suspicious
        return ActionReview(allowed=allowed, reason="suspicious" if not allowed else "ok")

    def register_suspect_event(self, agent_id: str, data: dict) -> None:
        self._append_tamper_evident_log(f"suspect:{agent_id}:{data}")

    def _append_tamper_evident_log(self, event: str) -> None:
        prev = self.audit_log[-1] if self.audit_log else "root"
        digest = sha256(f"{prev}|{event}".encode()).hexdigest()
        self.audit_log.append(f"{event}|{digest}")


JudgeSystem = JusticeSystem

justice = JusticeSystem(CoreEnergyLedger())
