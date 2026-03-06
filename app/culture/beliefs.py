from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BeliefMovement:
    name: str
    doctrine: str
    founder_id: str
    loyalty: Dict[str, float] = field(default_factory=dict)

    def recruit(self, agent_id: str, charisma: float) -> float:
        self.loyalty[agent_id] = min(1.0, self.loyalty.get(agent_id, 0.0) + 0.1 + charisma * 0.2)
        return self.loyalty[agent_id]

    def loyalty_bonus(self, agent_id: str) -> float:
        return self.loyalty.get(agent_id, 0.0) * 0.05


class BeliefEngine:
    def __init__(self) -> None:
        self.movements: Dict[str, BeliefMovement] = {}

    def found_movement(self, name: str, doctrine: str, founder_id: str) -> BeliefMovement:
        movement = BeliefMovement(name=name, doctrine=doctrine, founder_id=founder_id)
        self.movements[name] = movement
        return movement
