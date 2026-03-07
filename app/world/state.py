from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Mapping

from app.models import Resource, World


@dataclass
class GlobalState:
    energy_price: float
    economic_indicators: Dict[str, float]
    market_volumes: Dict[str, float]
    reputation_rankings: Dict[str, float]
    institution_power: Dict[str, float]
    crisis_signals: Dict[str, float]

    @classmethod
    def from_world(cls, world: World) -> "GlobalState":
        company_cash = [company.cash for company in world.companies.values()]
        avg_company_cash = mean(company_cash) if company_cash else 0.0
        bankrupt_companies = sum(1 for c in world.companies.values() if c.cash < 0)

        market_volumes = {
            resource.value: max(0.0, 10000.0 - amount)
            for resource, amount in world.global_resources.items()
        }

        reputation_rankings = {
            agent.id: max(0.0, min(100.0, 50.0 + agent.wallet / 10.0))
            for agent in world.agents.values()
        }

        institution_power = {
            "bank": max(0.0, min(100.0, world.bank.reserve / 1000.0)),
            "corporations": float(len(world.companies) * 5),
            "state": 40.0 + min(40.0, float(world.tick_count) * 0.1),
        }

        crisis_signals = {
            "energy_shortage": 1.0 if world.global_resources[Resource.ENERGY] < 2000 else 0.0,
            "bank_run": 1.0 if world.bank.reserve < 5000 else 0.0,
            "economic_collapse": 1.0 if bankrupt_companies > max(3, len(world.companies) // 2) else 0.0,
            "oracle_failure": 0.2 if world.tick_count % 25 == 0 and world.tick_count > 0 else 0.0,
            "war": 0.1 if len(world.companies) > 8 else 0.0,
        }

        return cls(
            energy_price=world.market_prices[Resource.ENERGY],
            economic_indicators={
                "gdp_proxy": avg_company_cash * max(1, len(world.companies)),
                "inflation_proxy": world.market_prices[Resource.ENERGY] / 4.0,
                "liquidity": world.bank.reserve,
            },
            market_volumes=market_volumes,
            reputation_rankings=reputation_rankings,
            institution_power=institution_power,
            crisis_signals=crisis_signals,
        )


def partial_view(
    global_state: GlobalState,
    agent_id: str,
    confidence: float,
    known_agents: Mapping[str, float],
) -> Dict[str, object]:
    confidence = max(0.05, min(1.0, confidence))

    visible_reputations = {
        other_id: score
        for other_id, score in global_state.reputation_rankings.items()
        if other_id == agent_id or other_id in known_agents
    }

    blurred_crisis_signals = {
        name: value * confidence
        for name, value in global_state.crisis_signals.items()
    }

    partial_market = {
        resource: volume * confidence
        for resource, volume in global_state.market_volumes.items()
    }

    return {
        "energy_price": global_state.energy_price * (0.8 + 0.2 * confidence),
        "economic_indicators": {
            k: v * confidence for k, v in global_state.economic_indicators.items()
        },
        "market_volumes": partial_market,
        "reputation_rankings": visible_reputations,
        "institution_power": {
            k: v * (0.7 + 0.3 * confidence)
            for k, v in global_state.institution_power.items()
        },
        "crisis_signals": blurred_crisis_signals,
    }
