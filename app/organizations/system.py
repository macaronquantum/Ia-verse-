from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import uuid4

from app.economy.markets import Order, OrderBook


@dataclass
class Organization:
    id: str
    name: str
    kind: str  # company/guild/coalition/state
    treasury: float
    workers: List[str] = field(default_factory=list)
    shares_outstanding: float = 0.0
    valuation: float = 0.0


class OrganizationSystem:
    def __init__(self) -> None:
        self.organizations: Dict[str, Organization] = {}
        self.equity_books: Dict[str, OrderBook] = {}

    def create_company(self, name: str, treasury: float = 100.0) -> Organization:
        org = Organization(id=str(uuid4()), name=name, kind="company", treasury=treasury)
        self.organizations[org.id] = org
        return org

    def create_guild(self, name: str, treasury: float = 50.0) -> Organization:
        org = Organization(id=str(uuid4()), name=name, kind="guild", treasury=treasury)
        self.organizations[org.id] = org
        return org

    def create_state(self, name: str, treasury: float) -> Organization:
        if treasury < 2000:
            raise ValueError("state creation is extremely expensive")
        org = Organization(id=str(uuid4()), name=name, kind="state", treasury=treasury)
        self.organizations[org.id] = org
        return org

    def ipo(self, org_id: str, shares: float, listing_price: float, underwriter_bank_id: str) -> None:
        org = self.organizations[org_id]
        if org.kind != "company":
            raise ValueError("only companies can issue equity")
        org.shares_outstanding += shares
        org.valuation = shares * listing_price
        book = OrderBook(symbol=f"EQ-{org_id}")
        book.asks.append(Order(agent_id=underwriter_bank_id, side="sell", price=listing_price, quantity=shares))
        self.equity_books[org_id] = book

    def trade_equity(self, org_id: str, order: Order):
        if org_id not in self.equity_books:
            raise ValueError("company is not listed")
        trades = self.equity_books[org_id].place_order(order)
        if trades:
            last_price = trades[-1].price
            self.organizations[org_id].valuation = self.organizations[org_id].shares_outstanding * last_price
        return trades

    def hire_worker(self, org_id: str, worker_id: str) -> None:
        self.organizations[org_id].workers.append(worker_id)

    def fire_worker(self, org_id: str, worker_id: str) -> None:
        org = self.organizations[org_id]
        if worker_id in org.workers:
            org.workers.remove(worker_id)
