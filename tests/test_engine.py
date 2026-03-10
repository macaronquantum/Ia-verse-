import asyncio

from app.agents.factory import AgentFactory
from app.api_gateway.gateway import APIGateway
from app.economy.markets import MarketSystem
from app.economy.system import EconomyCoordinator
from app.energy.core import EnergyLedger
from app.institutions.entities import CentralBank, InstitutionCoordinator
from app.justice.system import JusticeSystem
from app.llm.adapters import HybridLLMAdapter
from app.observability.metrics import MetricsCollector
from app.simulation.engine import SimulationEngine


def test_simulation_tick_updates_metrics_and_prices():
    async def scenario() -> None:
        ledger = EnergyLedger()
        llm = HybridLLMAdapter(APIGateway())
        factory = AgentFactory(ledger, llm)
        market = MarketSystem()
        economy = EconomyCoordinator(market=market, ledger=ledger)
        institutions = InstitutionCoordinator(CentralBank(ledger), JusticeSystem())
        engine = SimulationEngine(economy=economy, institutions=institutions, metrics=MetricsCollector(), tick_seconds=0)

        a1 = factory.create("citizen", name="Alice", goals=["earn"], skills={"labor"})
        a2 = factory.create("company", name="Acme", goals=["profit"], skills={"produce", "trade"})
        engine.register(a1)
        engine.register(a2)

        report = await engine.run_tick()

        assert report["tick"] == 1
        assert report["valid_actions"] >= 2
        assert "agent_population" in report["metrics"]["gauges"]

    asyncio.run(scenario())
