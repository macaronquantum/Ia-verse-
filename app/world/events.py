from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorldEvent:
    kind: str
    severity: float
    description: str
