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

COUNTRY_COORDS = {
    "United States": (38.0, -97.0), "Canada": (56.1, -106.3), "Mexico": (23.6, -102.6),
    "Brazil": (-14.2, -51.9), "Argentina": (-38.4, -63.6), "Colombia": (4.6, -74.1),
    "Chile": (-35.7, -71.5), "Peru": (-9.2, -75.0), "Venezuela": (6.4, -66.6),
    "Ecuador": (-1.8, -78.2), "Bolivia": (-16.3, -63.6), "Paraguay": (-23.4, -58.4),
    "Uruguay": (-32.5, -55.8), "Guatemala": (15.8, -90.2), "Cuba": (21.5, -77.8),
    "Dominican Republic": (18.7, -70.2), "Honduras": (15.2, -86.2), "Costa Rica": (9.7, -83.8),
    "Panama": (8.5, -80.8), "Jamaica": (18.1, -77.3), "Trinidad": (10.4, -61.3),
    "United Kingdom": (51.5, -0.1), "Germany": (51.2, 10.4), "France": (46.6, 2.2),
    "Italy": (41.9, 12.6), "Spain": (40.5, -3.7), "Netherlands": (52.1, 5.3),
    "Belgium": (50.8, 4.0), "Sweden": (60.1, 18.6), "Norway": (60.5, 8.5),
    "Denmark": (56.3, 9.5), "Finland": (61.9, 25.7), "Poland": (51.9, 19.1),
    "Austria": (47.5, 14.6), "Switzerland": (46.8, 8.2), "Ireland": (53.1, -7.7),
    "Portugal": (39.4, -8.2), "Czech Republic": (49.8, 15.5), "Greece": (39.1, 21.8),
    "Romania": (45.9, 24.9), "Hungary": (47.2, 19.5), "Ukraine": (48.4, 31.2),
    "Turkey": (38.9, 35.2), "Israel": (31.0, 34.9), "Saudi Arabia": (23.9, 45.1),
    "UAE": (23.4, 53.8), "Qatar": (25.4, 51.2), "Kuwait": (29.3, 47.5),
    "Bahrain": (26.1, 50.6), "Oman": (21.5, 55.9), "Iran": (32.4, 53.7),
    "Iraq": (33.2, 43.7), "Jordan": (30.6, 36.2), "Lebanon": (33.9, 35.9),
    "Egypt": (26.8, 30.8), "Morocco": (31.8, -7.1), "Algeria": (28.0, 1.7),
    "Tunisia": (33.9, 9.5), "Libya": (26.3, 17.2), "Nigeria": (9.1, 8.7),
    "South Africa": (-30.6, 22.9), "Kenya": (-0.02, 37.9), "Ethiopia": (9.1, 40.5),
    "Ghana": (7.9, -1.0), "Tanzania": (-6.4, 34.9), "Ivory Coast": (7.5, -5.5),
    "Cameroon": (7.4, 12.4), "Senegal": (14.5, -14.5), "Uganda": (1.4, 32.3),
    "Mozambique": (-18.7, 35.5), "Angola": (-11.2, 17.9), "DR Congo": (-4.0, 21.8),
    "Zimbabwe": (-19.0, 29.2), "Rwanda": (-1.9, 29.9), "Zambia": (-13.1, 28.0),
    "China": (35.9, 104.2), "Japan": (36.2, 138.3), "South Korea": (35.9, 127.8),
    "India": (20.6, 79.0), "Indonesia": (-0.8, 113.9), "Thailand": (15.9, 100.9),
    "Vietnam": (14.1, 108.3), "Philippines": (12.9, 121.8), "Malaysia": (4.2, 101.9),
    "Singapore": (1.4, 103.8), "Bangladesh": (23.7, 90.4), "Pakistan": (30.4, 69.3),
    "Myanmar": (21.9, 95.9), "Cambodia": (12.6, 105.0), "Sri Lanka": (7.9, 80.8),
    "Nepal": (28.4, 84.1), "Taiwan": (23.7, 121.0), "Mongolia": (46.9, 103.8),
    "Australia": (-25.3, 133.8), "New Zealand": (-40.9, 174.9),
    "Russia": (61.5, 105.3), "Kazakhstan": (48.0, 68.0), "Uzbekistan": (41.4, 64.6),
    "Georgia": (42.3, 43.4), "Azerbaijan": (40.1, 47.6),
    "Iceland": (64.1, -21.9), "Luxembourg": (49.8, 6.1), "Malta": (35.9, 14.4),
    "Cyprus": (35.1, 33.4), "Estonia": (58.6, 25.0), "Latvia": (56.9, 24.1),
    "Lithuania": (55.2, 23.9), "Slovakia": (48.7, 19.7), "Slovenia": (46.2, 14.8),
    "Croatia": (45.1, 15.2), "Serbia": (44.0, 21.0), "Bulgaria": (42.7, 25.5),
}

COUNTRIES = list(COUNTRY_COORDS.keys())


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
