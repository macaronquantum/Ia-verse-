from __future__ import annotations

from dataclasses import dataclass, field

from app.energy.core import CoreEnergyLedger


@dataclass
class DailySettlementSystem:
    ledger: CoreEnergyLedger
    pending_batches: list[dict[str, float]] = field(default_factory=list)

    def run_daily_settlement(self) -> dict[str, float]:
        batch = self.ledger.daily_settlement_batch()
        self.pending_batches.append(batch)
        return batch
