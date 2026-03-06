from __future__ import annotations

from dataclasses import dataclass, field


CONTINENTS = ["africa", "asia", "europe", "north_america", "south_america"]


@dataclass
class CentralBank:
    bank_id: str
    continent: str
    currency: str
    core_energy_reserve: float
    intelligence_weight: float = 3.0


@dataclass
class State:
    state_id: str
    continent: str
    tax_rate: float = 0.2
    treasury_balance: float = 0.0

    def collect_tax(self, gross: float) -> float:
        collected = gross * self.tax_rate
        self.treasury_balance += collected
        return collected


@dataclass
class Bank:
    bank_id: str
    deposits: float = 0.0
    loans: dict[str, float] = field(default_factory=dict)


def bootstrap_central_banks(total_core_energy: float = 10000.0) -> list[CentralBank]:
    per_bank = total_core_energy / len(CONTINENTS)
    return [
        CentralBank(bank_id=f"cb_{name}", continent=name, currency=name[:3].upper(), core_energy_reserve=per_bank)
        for name in CONTINENTS
    ]
