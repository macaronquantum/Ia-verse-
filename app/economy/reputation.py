from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ReputationProfile:
    score: float = 0.5
    successful_transactions: int = 0
    defaults: int = 0
    judicial_penalties: int = 0
    economic_contributions: float = 0.0
    transparency: float = 0.5


@dataclass
class ReputationEngine:
    profiles: Dict[str, ReputationProfile] = field(default_factory=dict)

    def ensure(self, agent_id: str) -> ReputationProfile:
        self.profiles.setdefault(agent_id, ReputationProfile())
        return self.profiles[agent_id]

    def record_transaction(self, agent_id: str, success: bool) -> float:
        p = self.ensure(agent_id)
        if success:
            p.successful_transactions += 1
            p.score += 0.01
        else:
            p.defaults += 1
            p.score -= 0.05
        p.score = self._clamp(p.score)
        return p.score

    def record_judgment(self, agent_id: str, severe: bool = False) -> float:
        p = self.ensure(agent_id)
        p.judicial_penalties += 1
        p.score -= 0.08 if severe else 0.04
        p.score = self._clamp(p.score)
        return p.score

    def record_economic_contribution(self, agent_id: str, value: float) -> float:
        p = self.ensure(agent_id)
        p.economic_contributions += value
        p.score += min(value / 10_000, 0.05)
        p.score = self._clamp(p.score)
        return p.score

    def apply_transparency_adjustment(self, agent_id: str, transparency: float, can_lie: bool = True) -> float:
        p = self.ensure(agent_id)
        p.transparency = transparency
        delta = (transparency - 0.5) * 0.1
        if can_lie and transparency < 0.4:
            delta -= 0.03
        p.score = self._clamp(p.score + delta)
        return p.score

    def counterparty_credit_limit_multiplier(self, agent_id: str) -> float:
        p = self.ensure(agent_id)
        return round(0.5 + p.score, 2)

    def price_impact_multiplier(self, agent_id: str) -> float:
        p = self.ensure(agent_id)
        return round(max(0.5, 1.5 - p.score), 2)

    @staticmethod
    def _clamp(score: float) -> float:
        return max(0.0, min(1.0, score))
