"""Minimal metric counters for startup/autonomy flows."""

from __future__ import annotations


class Metrics:
    def __init__(self) -> None:
        self.counters = {
            "agent_created_count": 0,
            "business_created_count": 0,
            "tool_published_count": 0,
            "human_jobs_posted": 0,
            "coreenergy_flow": 0.0,
        }

    def inc(self, name: str, amount: float = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount
