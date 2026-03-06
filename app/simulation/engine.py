from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import monotonic

from app.agents.base import BaseAgent
from app.economy.system import EconomyCoordinator
from app.institutions.entities import InstitutionCoordinator
from app.observability.metrics import MetricsCollector


@dataclass
class SimulationEngine:
    economy: EconomyCoordinator
    institutions: InstitutionCoordinator
    metrics: MetricsCollector
    tick_seconds: float = 5.0
    tick_count: int = 0
    agents: dict[str, BaseAgent] = field(default_factory=dict)

    def register(self, agent: BaseAgent) -> None:
        self.agents[agent.agent_id] = agent

    async def run_tick(self) -> dict[str, object]:
        start = monotonic()
        environment = {"market_snapshot": self.economy.market.snapshot(), "tick": self.tick_count}

        action_batches = await asyncio.gather(*(agent.on_tick(environment) for agent in self.agents.values()))
        valid_actions = 0
        for batch in action_batches:
            for action in batch:
                if self.economy.validate_and_apply_action(action):
                    valid_actions += 1

        prices = self.economy.tick()
        total_energy = sum(self.economy.ledger.distribution().values())
        market_shares = self._estimate_market_shares()
        institution_report = self.institutions.tick(
            total_energy=total_energy,
            agents=list(self.agents.keys()),
            market_shares=market_shares,
        )

        self.tick_count += 1
        duration = monotonic() - start
        self.metrics.inc("ticks", 1)
        self.metrics.inc("actions_valid", valid_actions)
        self.metrics.set_gauge("agent_population", len(self.agents))
        self.metrics.set_gauge("tick_duration_seconds", duration)
        self.metrics.set_gauge("total_energy", total_energy)

        return {
            "tick": self.tick_count,
            "prices": prices,
            "valid_actions": valid_actions,
            "institutions": institution_report,
            "metrics": self.metrics.snapshot(),
        }

    async def run_forever(self) -> None:
        while True:
            started = monotonic()
            await self.run_tick()
            elapsed = monotonic() - started
            await asyncio.sleep(max(0.0, self.tick_seconds - elapsed))

    def _estimate_market_shares(self) -> dict[str, float]:
        balances = self.economy.ledger.distribution()
        total = sum(max(v, 0.0) for v in balances.values()) or 1.0
        return {k: max(v, 0.0) / total for k, v in balances.items() if k in self.agents}
