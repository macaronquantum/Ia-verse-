from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Dispute:
    claimant: str
    respondent: str
    reason: str


@dataclass
class JusticeSystem:
    disputes: list[Dispute] = field(default_factory=list)
    anti_monopoly_threshold: float = 0.55
    rulings: list[str] = field(default_factory=list)

    def file_dispute(self, dispute: Dispute) -> None:
        self.disputes.append(dispute)

    def inspect_market_share(self, shares: dict[str, float]) -> list[str]:
        flags = [agent for agent, share in shares.items() if share > self.anti_monopoly_threshold]
        for offender in flags:
            self.rulings.append(f"antitrust action on {offender}")
        return flags

    def tick(self) -> list[str]:
        if not self.disputes:
            return []
        results = [f"resolved:{d.claimant}->{d.respondent}:{d.reason}" for d in self.disputes]
        self.rulings.extend(results)
        self.disputes.clear()
        return results
