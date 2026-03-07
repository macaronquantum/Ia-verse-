from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BeliefSystem:
    ideology_scores: Dict[str, float] = field(default_factory=dict)
    religion_intensity: float = 0.0
    memes: Dict[str, float] = field(default_factory=dict)

    def form_ideology(self, name: str, coherence: float) -> None:
        self.ideology_scores[name] = max(0.0, self.ideology_scores.get(name, 0.0) + coherence)

    def emerge_religion(self, existential_pressure: float) -> None:
        self.religion_intensity = min(1.0, self.religion_intensity + max(0.0, existential_pressure) * 0.1)

    def spread_meme(self, meme: str, transmission_power: float) -> None:
        current = self.memes.get(meme, 0.0)
        self.memes[meme] = min(1.0, current + max(0.0, transmission_power) * 0.2)
