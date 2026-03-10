from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Opportunity:
    score: float
    tags: List[str]


class OpportunityEngine:
    def __init__(self) -> None:
        self.opportunities: List[Opportunity] = []

    def on_event(self, event: Dict) -> None:
        score = (event.get("urgency", 0) + max(event.get("sentiment", 0), 0)) * max(len(event.get("topic_tags", [])), 1)
        self.opportunities.append(Opportunity(score=score, tags=event.get("topic_tags", [])))
