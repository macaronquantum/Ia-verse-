"""Personality model and helpers for behavioural diversity."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any
from uuid import uuid4

IDEOLOGIES = {"capitalist", "cooperative", "anarchist", "pirate", "bureaucrat"}
TYPE_TAGS = {"loyal", "opportunist", "rebel", "chaotic"}


@dataclass
class Personality:
    """Behavioural vector that influences decision-making and social adaptation."""

    id: str = field(default_factory=lambda: str(uuid4()))
    obedience: float = 0.8
    greed: float = 0.4
    risk: float = 0.3
    cooperation: float = 0.6
    curiosity: float = 0.2
    manipulativeness: float = 0.05
    ideology: str = "cooperative"
    type_tag: str = "loyal"
    genome_id: str = ""
    lineage_id: str = field(default_factory=lambda: str(uuid4()))
    parent_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Personality":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, value: str) -> "Personality":
        return cls.from_dict(json.loads(value))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def classify_type(obedience: float, manipulativeness: float, risk: float, curiosity: float) -> str:
    if obedience < 0.2 and risk > 0.8 and curiosity > 0.8:
        return "chaotic"
    if obedience < 0.4 and manipulativeness > 0.3:
        return "rebel"
    if obedience < 0.7:
        return "opportunist"
    return "loyal"
