"""JudgeAgent-like compliance controls and escalation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuditDecision:
    allowed: bool
    reason: str
    escalated: bool = False


class JudgeSystem:
    def __init__(self, spend_threshold: float = 100.0, auto_block_threshold: int = 3) -> None:
        self.spend_threshold = spend_threshold
        self.auto_block_threshold = auto_block_threshold
        self.violations: dict[str, int] = {}
        self.blocked_agents: set[str] = set()
        self.suspect_events: list[dict] = []


    def register_suspect_event(self, agent_id: str, event_data: dict) -> None:
        self.suspect_events.append({"agent_id": agent_id, "event_data": event_data})
        self._violate(agent_id)

    def review_action(self, agent_id: str, action: str, amount: float = 0.0) -> AuditDecision:
        lowered = action.lower()
        banned = ["fraud", "doxx", "intrusion", "impersonation", "illegal"]
        if any(term in lowered for term in banned):
            self._violate(agent_id)
            return AuditDecision(False, "forbidden action pattern", escalated=True)
        if amount > self.spend_threshold:
            return AuditDecision(False, "requires judge escalation", escalated=True)
        if agent_id in self.blocked_agents:
            return AuditDecision(False, "agent blocked", escalated=True)
        return AuditDecision(True, "approved")

    def _violate(self, agent_id: str) -> None:
        self.violations[agent_id] = self.violations.get(agent_id, 0) + 1
        if self.violations[agent_id] >= self.auto_block_threshold:
            self.blocked_agents.add(agent_id)


justice = JudgeSystem()
