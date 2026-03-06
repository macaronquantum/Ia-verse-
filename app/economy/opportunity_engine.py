"""Opportunity detection from market signals, tool shortages and world events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Opportunity:
    id: str
    type: str
    desc: str
    estimated_cost: float
    estimated_revenue: float
    required_skills: list[str]
    risk_score: float
    time_to_mvp: int

    @property
    def score(self) -> float:
        return (self.estimated_revenue - self.estimated_cost) * (1 - self.risk_score)


class OpportunityEngine:
    def __init__(self, threshold: float = 10.0) -> None:
        self.threshold = threshold

    def get_opportunities(self, agent_id: str, horizon_hours: int, state: dict) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        shortages = state.get("tool_shortages", [])
        for missing in shortages:
            opp = Opportunity(
                id=str(uuid4()),
                type="SaaS B2B",
                desc=f"Build missing tool: {missing}",
                estimated_cost=20,
                estimated_revenue=80 + horizon_hours * 0.5,
                required_skills=["dev", "ops"],
                risk_score=0.2,
                time_to_mvp=24,
            )
            if opp.score > self.threshold:
                opportunities.append(opp)

        if state.get("human_demand", 0) > 0:
            opportunities.append(
                Opportunity(
                    id=str(uuid4()),
                    type="managed service",
                    desc="Human-mediated service for incoming demand",
                    estimated_cost=30,
                    estimated_revenue=75,
                    required_skills=["marketer"],
                    risk_score=0.3,
                    time_to_mvp=12,
                )
            )
        return sorted(opportunities, key=lambda x: x.score, reverse=True)

    def opportunity_runner(self, states: list[dict]) -> list[Opportunity]:
        collected: list[Opportunity] = []
        for s in states:
            collected.extend(self.get_opportunities(s.get("agent_id", "system"), 24, s))
        return collected
