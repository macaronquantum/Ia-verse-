from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CentralBankAgent:
    id: str
    continent: str
    transparency_score: float = 0.9


class InstitutionBootstrap:
    DEFAULT_CONTINENTS = ["Africa", "Americas", "Asia", "Europe", "Oceania"]

    def __init__(self, continents: List[str] | None = None) -> None:
        self.continents = continents or self.DEFAULT_CONTINENTS

    def create_initial_central_banks(self) -> List[CentralBankAgent]:
        return [
            CentralBankAgent(id=f"cb-{c.lower()}", continent=c)
            for c in self.continents
        ]
