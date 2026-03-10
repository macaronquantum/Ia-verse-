from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.tool_manifest import ToolManifest


class Resource(str, Enum):
    ENERGY = "energy"
    FOOD = "food"
    METAL = "metal"
    KNOWLEDGE = "knowledge"


@dataclass
class Loan:
    id: str
    borrower_id: str
    amount: float
    interest_rate: float
    remaining: float


@dataclass
class Account:
    owner_id: str
    balance: float = 0.0


AGENT_TYPES = ["central_bank", "bank", "company", "state", "judge", "energy_provider", "trader", "citizen"]

COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France", "Japan", "China",
    "Brazil", "India", "Australia", "Canada", "Switzerland", "Singapore",
    "South Korea", "South Africa", "Mexico", "Russia", "Italy", "Spain",
    "Netherlands", "Sweden", "Norway", "UAE", "Saudi Arabia", "Nigeria",
]

COUNTRY_COORDS = {
    "United States": (38.0, -97.0), "United Kingdom": (51.5, -0.1), "Germany": (51.2, 10.4),
    "France": (46.6, 2.2), "Japan": (36.2, 138.3), "China": (35.9, 104.2),
    "Brazil": (-14.2, -51.9), "India": (20.6, 79.0), "Australia": (-25.3, 133.8),
    "Canada": (56.1, -106.3), "Switzerland": (46.8, 8.2), "Singapore": (1.4, 103.8),
    "South Korea": (35.9, 127.8), "South Africa": (-30.6, 22.9), "Mexico": (23.6, -102.6),
    "Russia": (61.5, 105.3), "Italy": (41.9, 12.6), "Spain": (40.5, -3.7),
    "Netherlands": (52.1, 5.3), "Sweden": (60.1, 18.6), "Norway": (60.5, 8.5),
    "UAE": (23.4, 53.8), "Saudi Arabia": (23.9, 45.1), "Nigeria": (9.1, 8.7),
}


def _assign_agent_type(name: str) -> str:
    import random
    n = name.lower()
    if "bank" in n and "central" in n:
        return "central_bank"
    if "bank" in n:
        return "bank"
    if "judge" in n or "justice" in n:
        return "judge"
    if "state" in n or "gov" in n:
        return "state"
    if "energy" in n or "power" in n:
        return "energy_provider"
    return random.choice(["trader", "company", "citizen", "bank"])


def _assign_country() -> str:
    import random
    return random.choice(COUNTRIES)


@dataclass
class Agent:
    id: str
    name: str
    wallet: float = 100.0
    inventory: Dict[Resource, float] = field(default_factory=lambda: {r: 10.0 for r in Resource})
    company_id: Optional[str] = None
    agent_type: str = ""
    country: str = ""
    influence_score: float = 0.0
    risk_score: float = 0.0
    personality: str = ""
    wealth_history: List[float] = field(default_factory=list)
    decision_log: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.agent_type:
            self.agent_type = _assign_agent_type(self.name)
        if not self.country:
            self.country = _assign_country()
        if not self.personality:
            import random
            self.personality = random.choice(["aggressive", "conservative", "balanced", "speculative", "cautious"])


@dataclass
class Company:
    id: str
    name: str
    owner_agent_id: str
    cash: float = 200.0
    inventory: Dict[Resource, float] = field(default_factory=lambda: {r: 5.0 for r in Resource})
    productivity: float = 1.0


@dataclass
class Bank:
    id: str
    accounts: Dict[str, Account] = field(default_factory=dict)
    loans: Dict[str, Loan] = field(default_factory=dict)
    reserve: float = 100000.0
    base_interest_rate: float = 0.02

    def ensure_account(self, owner_id: str) -> Account:
        if owner_id not in self.accounts:
            self.accounts[owner_id] = Account(owner_id=owner_id, balance=0.0)
        return self.accounts[owner_id]

    def deposit(self, owner_id: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        account = self.ensure_account(owner_id)
        account.balance += amount
        self.reserve += amount

    def withdraw(self, owner_id: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        account = self.ensure_account(owner_id)
        if account.balance < amount:
            raise ValueError("insufficient account balance")
        if self.reserve < amount:
            raise ValueError("bank reserve too low")
        account.balance -= amount
        self.reserve -= amount

    def issue_loan(self, borrower_id: str, amount: float, interest_rate: Optional[float] = None) -> Loan:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if self.reserve < amount:
            raise ValueError("bank reserve too low")
        rate = interest_rate if interest_rate is not None else self.base_interest_rate
        loan = Loan(
            id=str(uuid4()),
            borrower_id=borrower_id,
            amount=amount,
            interest_rate=rate,
            remaining=amount,
        )
        self.loans[loan.id] = loan
        self.reserve -= amount
        self.ensure_account(borrower_id).balance += amount
        return loan

    def repay_loan(self, borrower_id: str, loan_id: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        loan = self.loans.get(loan_id)
        if loan is None or loan.borrower_id != borrower_id:
            raise ValueError("loan not found for borrower")
        account = self.ensure_account(borrower_id)
        if account.balance < amount:
            raise ValueError("insufficient account balance")

        paid = min(amount, loan.remaining)
        account.balance -= paid
        loan.remaining -= paid
        self.reserve += paid

        if loan.remaining <= 1e-9:
            del self.loans[loan_id]

    def apply_interest(self) -> None:
        for loan in self.loans.values():
            loan.remaining *= 1 + loan.interest_rate


@dataclass
class World:
    id: str
    name: str
    tick_count: int = 0
    agents: Dict[str, Agent] = field(default_factory=dict)
    companies: Dict[str, Company] = field(default_factory=dict)
    bank: Bank = field(default_factory=lambda: Bank(id=str(uuid4())))
    market_prices: Dict[Resource, float] = field(
        default_factory=lambda: {
            Resource.ENERGY: 4.0,
            Resource.FOOD: 3.0,
            Resource.METAL: 6.0,
            Resource.KNOWLEDGE: 8.0,
        }
    )
    global_resources: Dict[Resource, float] = field(
        default_factory=lambda: {
            Resource.ENERGY: 10000.0,
            Resource.FOOD: 10000.0,
            Resource.METAL: 10000.0,
            Resource.KNOWLEDGE: 10000.0,
        }
    )
    event_log: List[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        self.event_log.append(f"[tick {self.tick_count}] {message}")


@dataclass
class AgentGoal:
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    description: str = ""
    priority: float = 1.0
    status: str = "active"
    created_tick: int = 0
    completed_tick: Optional[int] = None


@dataclass
class AgentTask:
    id: str = field(default_factory=lambda: str(uuid4()))
    goal_id: str = ""
    agent_id: str = ""
    description: str = ""
    status: str = "pending"
    result: Optional[str] = None


@dataclass
class AgentMemoryRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    kind: str = ""
    content: str = ""
    tick: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentTransaction:
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    counterparty_id: str = ""
    amount: float = 0.0
    kind: str = ""
    tick: int = 0


@dataclass
class AgentBusiness:
    id: str = field(default_factory=lambda: str(uuid4()))
    owner_agent_id: str = ""
    name: str = ""
    industry: str = ""
    revenue: float = 0.0
    expenses: float = 0.0
    employees: List[str] = field(default_factory=list)


class AgentTier(str, Enum):
    WORKER = "worker"
    BUSINESS = "business"
    BANK = "bank"
    CENTRAL_BANK = "central_bank"


@dataclass
class AgentFinances:
    currency_balances: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentState:
    id: str
    name: str
    tier: AgentTier = AgentTier.WORKER
    core_energy: float = 10.0
    alive: bool = True
    finances: AgentFinances = field(default_factory=AgentFinances)


@dataclass
class Action:
    actor_id: str
    action_type: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    content: str = ""
    tick: int = 0
    read: bool = False
