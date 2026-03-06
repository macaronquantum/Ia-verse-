from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Strategy(str, Enum):
    SURVIVAL_BASIC = "survival_basic"
    PASSIVE_ACCUMULATION = "passive_accumulation"
    MARKET_ARBITRAGE = "market_arbitrage"
    MARKET_MAKING = "market_making"
    LEVERAGE_CREDIT_FARMING = "leverage_credit_farming"
    COMPANY_BUILDER = "company_builder"
    FINANCIAL_ENGINEER = "financial_engineer"
    INFRASTRUCTURE_PROVIDER = "infrastructure_provider"
    ORACLE_PROVIDER = "oracle_provider"
    REGULATORY_CAPTURE = "regulatory_capture"
    COALITION_BUILDING = "coalition_building"
    PREDATOR = "predator"
    RESEARCH_TECH_LEAD = "research_tech_lead"
    RELIGIOUS_MOVEMENT_FOUNDER = "religious_movement_founder"
    EXPLORER = "explorer"


@dataclass
class StrategyContext:
    energy_balance: float
    profitability: float
    risk_tolerance: float
    reputation_score: float
    market_volatility: float
    liquidity: float
    curiosity: float = 0.2
    power_score: float = 0.0


@dataclass
class StrategyManager:
    """Choisit une stratégie en respectant la hiérarchie des objectifs:
    1) survivre, 2) augmenter le pouvoir, 3) sens/curiosité.
    """

    current_strategy: Strategy = Strategy.SURVIVAL_BASIC
    strategy_history: List[Strategy] = field(default_factory=list)

    def choose_strategy(self, ctx: StrategyContext) -> Strategy:
        if ctx.energy_balance < 15:
            chosen = Strategy.SURVIVAL_BASIC
        elif ctx.reputation_score < 0.2:
            chosen = Strategy.PASSIVE_ACCUMULATION
        elif ctx.market_volatility > 0.75 and ctx.risk_tolerance > 0.65:
            chosen = Strategy.MARKET_ARBITRAGE
        elif ctx.liquidity > 0.8 and ctx.profitability > 0.5:
            chosen = Strategy.MARKET_MAKING
        elif ctx.power_score > 0.8 and ctx.reputation_score > 0.5:
            chosen = Strategy.REGULATORY_CAPTURE
        elif ctx.curiosity > 0.75 and ctx.energy_balance > 40:
            chosen = Strategy.EXPLORER
        elif ctx.profitability > 0.7:
            chosen = Strategy.COMPANY_BUILDER
        else:
            chosen = Strategy.RESEARCH_TECH_LEAD

        self.current_strategy = chosen
        self.strategy_history.append(chosen)
        return chosen

    def should_switch(self, ctx: StrategyContext) -> bool:
        if self.current_strategy == Strategy.SURVIVAL_BASIC:
            return ctx.energy_balance > 25 and ctx.profitability > 0.2
        return ctx.energy_balance < 10 or ctx.profitability < -0.1

    @staticmethod
    def available_strategies() -> Dict[str, str]:
        return {
            Strategy.SURVIVAL_BASIC.value: "Maintain minimum Core Energy to avoid death",
            Strategy.PASSIVE_ACCUMULATION.value: "Deposit and accrue interests",
            Strategy.MARKET_ARBITRAGE.value: "Exploit FX/spread inefficiencies",
            Strategy.MARKET_MAKING.value: "Provide order-book liquidity",
            Strategy.LEVERAGE_CREDIT_FARMING.value: "Borrow/lend for leveraged yield",
            Strategy.COMPANY_BUILDER.value: "Found or acquire companies",
            Strategy.FINANCIAL_ENGINEER.value: "Create structured products/derivatives",
            Strategy.INFRASTRUCTURE_PROVIDER.value: "Sell compute/storage services",
            Strategy.ORACLE_PROVIDER.value: "Sell external data feeds",
            Strategy.REGULATORY_CAPTURE.value: "Influence institutions for power",
            Strategy.COALITION_BUILDING.value: "Build guild/cartel alliances",
            Strategy.PREDATOR.value: "Hostile takeovers and raids",
            Strategy.RESEARCH_TECH_LEAD.value: "R&D to lower future costs",
            Strategy.RELIGIOUS_MOVEMENT_FOUNDER.value: "Build loyalty through belief systems",
            Strategy.EXPLORER.value: "Probe APIs/real world for value extraction",
        }
