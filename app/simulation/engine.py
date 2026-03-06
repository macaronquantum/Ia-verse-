from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SchedulingProfile:
    tier: str
    cadence_ticks: int


class AdaptiveScheduler:
    TIER_CADENCE = {"high": 1, "medium": 5, "low": 20}

    def __init__(self, tick_target_seconds: int = 5) -> None:
        self.tick_target_seconds = tick_target_seconds

    def profile_for_agent(self, energy: float, critical_role: bool = False) -> SchedulingProfile:
        if critical_role or energy > 200:
            tier = "high"
        elif energy > 50:
            tier = "medium"
        else:
            tier = "low"
        return SchedulingProfile(tier=tier, cadence_ticks=self.TIER_CADENCE[tier])

    def should_run(self, tick_count: int, profile: SchedulingProfile) -> bool:
        return tick_count % profile.cadence_ticks == 0

    def batch_llm_calls(self, calls: list[dict]) -> list[list[dict]]:
        # Batching simple par paquets de 8
        return [calls[i : i + 8] for i in range(0, len(calls), 8)]
