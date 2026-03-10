from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.base import AgentContext, BaseAgent
from app.agents.factory import build_agent
from app.economy.system import EconomyCoordinator, EconomySystem
from app.energy.core import CoreEnergyLedger, CoreEnergyMarket, EnergyError
from app.institutions.entities import InstitutionCoordinator, bootstrap_central_banks
from app.justice.judge import JudgeAI
from app.llm.adapters import ModelRouter
from app.observability.metrics import MetricsCollector
from app.models import Action, AgentState, AgentTier


@dataclass
class World:
    agents: dict[str, AgentState] = field(default_factory=dict)
    economy: EconomySystem = field(default_factory=EconomySystem)
    energy_ledger: CoreEnergyLedger = field(default_factory=CoreEnergyLedger)
    energy_market: CoreEnergyMarket = field(default_factory=CoreEnergyMarket)
    judge: JudgeAI = field(default_factory=JudgeAI)
    model_router: ModelRouter = field(default_factory=ModelRouter)
    tick_id: int = 0

    def bootstrap(self) -> None:
        for cb in bootstrap_central_banks():
            self.energy_ledger.balances[cb.bank_id] = cb.core_energy_reserve
        self.agents["w_1"] = AgentState("w_1", "Worker One", AgentTier.WORKER, core_energy=2.0)
        self.agents["c_1"] = AgentState("c_1", "Company One", AgentTier.BUSINESS, core_energy=4.0)
        self.agents["b_1"] = AgentState("b_1", "Bank One", AgentTier.BANK, core_energy=8.0)
        self.agents["cb_asia"] = AgentState("cb_asia", "CB Asia", AgentTier.CENTRAL_BANK, core_energy=20.0)


class SimulationEngine:
    def __init__(self, world: World | None = None, *, economy: EconomyCoordinator | None = None, institutions: InstitutionCoordinator | None = None, metrics: MetricsCollector | None = None, tick_seconds: float = 0.01):
        self.world = world or World()
        self.economy_coordinator = economy
        self.institutions = institutions
        self.metrics = metrics or MetricsCollector()
        self.tick_seconds = tick_seconds
        self._registered: list[BaseAgent] = []
        self._tick = 0

    # legacy API used by tests/test_engine.py
    def register(self, agent: BaseAgent) -> None:
        self._registered.append(agent)

    async def run_tick(self) -> dict:
        self._tick += 1
        valid = 0
        for agent in self._registered:
            actions = await agent.on_tick({"tick": self._tick, "market_snapshot": {}})
            for action in actions:
                if self.economy_coordinator and self.economy_coordinator.validate_and_apply_action(action):
                    valid += 1
        market_prices = self.economy_coordinator.tick() if self.economy_coordinator else {}
        gauges = {"agent_population": len(self._registered), "market_count": len(market_prices)}
        return {"tick": self._tick, "valid_actions": valid, "metrics": {"gauges": gauges}, "prices": market_prices}

    async def step(self) -> dict:
        self.world.tick_id += 1
        context = AgentContext(tick_id=self.world.tick_id, interest_rates=self.world.economy.interest_rates)
        agent_objs = [build_agent(s) for s in self.world.agents.values() if s.alive]
        await asyncio.gather(*(a.observe(context) for a in agent_objs))
        decisions = await asyncio.gather(*(a.decide(context) for a in agent_objs))
        actions: list[Action] = [action for batch in decisions for action in batch]
        rulings = self.world.judge.review(actions)
        self._apply_actions(actions)
        self._apply_energy_costs()
        self._enforce_death()
        return {"tick": self.world.tick_id, "actions": len(actions), "rulings": [r.__dict__ for r in rulings]}

    def _apply_actions(self, actions: list[Action]) -> None:
        for action in actions:
            if action.action_type == "monetary_policy":
                self.world.economy.apply_monetary_policy(action.payload["currency"], action.payload.get("rate_shift", 0.0))

    def _apply_energy_costs(self) -> None:
        for state in self.world.agents.values():
            if not state.alive:
                continue
            llm = self.world.model_router.for_tier(state.tier)
            result = llm.generate("Plan next economic action")
            state.core_energy -= result.tokens * llm.token_cost_energy
            try:
                self.world.energy_ledger.burn("cb_asia", 0.001)
            except EnergyError:
                pass

    def _enforce_death(self) -> None:
        for state in self.world.agents.values():
            if state.core_energy <= 0:
                state.alive = False

    async def run(self, ticks: int = 5, tick_seconds: float | None = None) -> list[dict]:
        out = []
        sleep_s = self.tick_seconds if tick_seconds is None else tick_seconds
        for _ in range(ticks):
            out.append(await self.step())
            await asyncio.sleep(sleep_s)
        return out


@dataclass
class SchedulingProfile:
    tick_interval: float = 1.0
    max_concurrent: int = 10
    priority_boost: float = 1.0


class AdaptiveScheduler:
    def __init__(self, profile: SchedulingProfile | None = None) -> None:
        self.profile = profile or SchedulingProfile()
        self._queue: list[dict] = []

    def schedule(self, task: dict) -> None:
        self._queue.append(task)

    def next_batch(self, max_items: int | None = None) -> list[dict]:
        limit = max_items or self.profile.max_concurrent
        batch = self._queue[:limit]
        self._queue = self._queue[limit:]
        return batch
