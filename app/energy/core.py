from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EnergyCostConfig:
    """Centralise tous les coûts énergétiques configurables.

    Les valeurs par défaut suivent les règles produit :
    - raisonnement local quasi-gratuit,
    - appels externes plus coûteux,
    - créations institutionnelles très coûteuses pour éviter la prolifération.
    """

    local_reasoning_tick: float = 0.01
    create_citizen_agent: float = 0.2
    create_bank_agent: float = 200.0
    create_state: float = 2000.0
    spawn_subjudge: float = 75.0
    llm_external_base: Dict[str, float] = field(
        default_factory=lambda: {
            "openai": 1.0,
            "anthropic": 1.2,
            "google": 0.9,
        }
    )


GLOBAL_ENERGY_COSTS = EnergyCostConfig()


class CoreEnergyLedger:
    """Ledger off-chain simplifié avec hook de settlement on-chain quotidien."""

    def __init__(self) -> None:
        self.balances: Dict[str, float] = {}
        self.pending_settlement: Dict[str, float] = {}

    def ensure(self, owner_id: str) -> None:
        self.balances.setdefault(owner_id, 0.0)
        self.pending_settlement.setdefault(owner_id, 0.0)

    def credit(self, owner_id: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("amount must be positive")
        self.ensure(owner_id)
        self.balances[owner_id] += amount
        self.pending_settlement[owner_id] += amount

    def burn(self, owner_id: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("amount must be positive")
        self.ensure(owner_id)
        if self.balances[owner_id] < amount:
            raise ValueError("insufficient core energy")
        self.balances[owner_id] -= amount
        self.pending_settlement[owner_id] -= amount

    def daily_settlement_batch(self) -> Dict[str, float]:
        """Retourne les deltas à régler on-chain (stub gateway Solana)."""
        batch = dict(self.pending_settlement)
        self.pending_settlement = {k: 0.0 for k in self.pending_settlement}
        return batch
