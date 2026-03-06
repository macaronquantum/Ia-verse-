from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AgentTier(str, Enum):
    WORKER = "tier1_worker"
    BUSINESS = "tier2_business"
    BANK = "tier3_bank"
    CENTRAL_BANK = "tier4_central_bank"
    SYSTEM = "tier5_system"


@dataclass
class Memory:
    objectives: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    relationships: Dict[str, float] = field(default_factory=dict)
    reputation: float = 0.5


@dataclass
class FinancialState:
    currency_balances: Dict[str, float] = field(default_factory=dict)
    debt: float = 0.0
    equity_positions: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentState:
    agent_id: str
    name: str
    tier: AgentTier
    alive: bool = True
    core_energy: float = 10.0
    memory: Memory = field(default_factory=Memory)
    finances: FinancialState = field(default_factory=FinancialState)
    organization_id: Optional[str] = None


@dataclass
class Action:
    actor_id: str
    action_type: str
    payload: Dict


@dataclass
class TickEvent:
    tick_id: int
    actions: List[Action] = field(default_factory=list)
