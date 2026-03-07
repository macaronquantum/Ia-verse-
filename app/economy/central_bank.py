from __future__ import annotations

from dataclasses import dataclass

from app.security.tamper_log import TamperEvidentLog


@dataclass
class CentralBank:
    core_energy_supply: float = 10000.0

    def __post_init__(self) -> None:
        self.log = TamperEvidentLog()

    def mint(self, amount: float) -> None:
        self.core_energy_supply += amount
        self.log.append("mint", str(amount))

    def burn(self, amount: float) -> None:
        self.core_energy_supply -= amount
        self.log.append("burn", str(amount))
