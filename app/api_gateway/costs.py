"""Billing and reserve primitives with tamper-evident transaction chain."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from time import time

from pydantic import BaseModel


class CostUpdate(BaseModel):
    key: str
    value: float


class CostCatalog:
    def __init__(self) -> None:
        self._costs: dict[str, float] = {
            "tool_call_base": 0.5,
            "tool_sandbox_second": 0.02,
        }

    def get(self, key: str, default: float = 0.0) -> float:
        return self._costs.get(key, default)

    def update(self, key: str, value: float) -> None:
        self._costs[key] = value

    def all(self) -> dict[str, float]:
        return dict(self._costs)


@dataclass
class LedgerEntry:
    owner_id: str
    kind: str
    amount: float
    status: str
    ts: float
    prev_hash: str
    hash: str


def estimate_cost(model: str, tokens: int) -> float:
    cost_per_k = {"local": 0.001, "openai": 0.03, "anthropic": 0.04}
    return cost_per_k.get(model, 0.01) * (tokens / 1000)


class BillingLedger:
    def __init__(self) -> None:
        self.balances: dict[str, float] = {}
        self.reserved: dict[str, float] = {}
        self.entries: list[LedgerEntry] = []

    def credit(self, owner_id: str, amount: float) -> None:
        self.balances[owner_id] = self.balances.get(owner_id, 0.0) + amount

    def preauthorize(self, owner_id: str, amount: float) -> str:
        if self.balances.get(owner_id, 0.0) < amount:
            raise ValueError("insufficient balance")
        self.balances[owner_id] -= amount
        self.reserved[owner_id] = self.reserved.get(owner_id, 0.0) + amount
        return self._append(owner_id, "preauth", amount, "reserved")

    def capture(self, owner_id: str, amount: float) -> str:
        if self.reserved.get(owner_id, 0.0) < amount:
            raise ValueError("insufficient reserved")
        self.reserved[owner_id] -= amount
        return self._append(owner_id, "capture", amount, "ok")

    def refund(self, owner_id: str, amount: float) -> str:
        if self.reserved.get(owner_id, 0.0) < amount:
            raise ValueError("insufficient reserved")
        self.reserved[owner_id] -= amount
        self.balances[owner_id] = self.balances.get(owner_id, 0.0) + amount
        return self._append(owner_id, "refund", amount, "ok")

    def _append(self, owner_id: str, kind: str, amount: float, status: str) -> str:
        prev = self.entries[-1].hash if self.entries else "GENESIS"
        payload = f"{owner_id}|{kind}|{amount}|{status}|{prev}|{time()}"
        h = sha256(payload.encode()).hexdigest()
        self.entries.append(LedgerEntry(owner_id, kind, amount, status, time(), prev, h))
        return h
