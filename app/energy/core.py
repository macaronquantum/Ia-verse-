from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


class EnergyError(RuntimeError):
    pass


@dataclass
class CoreEnergyLedger:
    total_supply: float = 10000.0
    balances: Dict[str, float] = field(default_factory=dict)

    def transfer(self, source: str, target: str, amount: float) -> None:
        if amount < 0:
            raise EnergyError("negative transfer")
        if self.balances.get(source, 0.0) < amount:
            raise EnergyError("insufficient energy")
        self.balances[source] -= amount
        self.balances[target] = self.balances.get(target, 0.0) + amount

    def burn(self, holder: str, amount: float) -> None:
        if self.balances.get(holder, 0.0) < amount:
            raise EnergyError("insufficient energy to burn")
        self.balances[holder] -= amount
        self.total_supply -= amount


@dataclass
class MintOracle:
    secret_salt: str

    def verify_proof_of_value(self, external_usd_value: float, proof: str) -> bool:
        return external_usd_value > 0 and proof.endswith(self.secret_salt[:3])

    def mint(self, ledger: CoreEnergyLedger, target: str, external_usd_value: float, proof: str) -> float:
        if not self.verify_proof_of_value(external_usd_value, proof):
            raise EnergyError("invalid proof of value")
        amount = external_usd_value / 1_000_000.0
        ledger.total_supply += amount
        ledger.balances[target] = ledger.balances.get(target, 0.0) + amount
        return amount


@dataclass
class CoreEnergyMarket:
    settlement_interval_ticks: int = 48
    internal_fx: dict[str, float] = field(default_factory=lambda: {"USD": 0.1, "EUR": 0.11})

    def quote(self, currency: str, amount: float) -> float:
        return amount * self.internal_fx[currency]
