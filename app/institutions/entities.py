from __future__ import annotations

from dataclasses import dataclass

from app.energy.core import EnergyLedger
from app.justice.system import JusticeSystem


@dataclass
class CentralBank:
    ledger: EnergyLedger
    liquidity_target: float = 1000.0
    system_account: str = "central_bank"

    def inject_liquidity(self, agents: list[str], amount_each: float = 1.0) -> None:
        for agent_id in agents:
            self.ledger.mint(agent_id, amount_each)

    def stabilize(self, total_energy: float, agents: list[str]) -> None:
        if total_energy < self.liquidity_target:
            self.inject_liquidity(agents, amount_each=2.0)


@dataclass
class InstitutionCoordinator:
    central_bank: CentralBank
    justice_system: JusticeSystem

    def tick(self, *, total_energy: float, agents: list[str], market_shares: dict[str, float]) -> dict[str, object]:
        self.central_bank.stabilize(total_energy, agents)
        antitrust = self.justice_system.inspect_market_share(market_shares)
        rulings = self.justice_system.tick()
        return {"antitrust_flags": antitrust, "rulings": rulings}
