from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


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


@dataclass
class Agent:
    id: str
    name: str
    wallet: float = 100.0
    inventory: Dict[Resource, float] = field(default_factory=lambda: {r: 10.0 for r in Resource})
    company_id: Optional[str] = None


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
