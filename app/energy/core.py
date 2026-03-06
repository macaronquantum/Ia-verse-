from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Hold:
    hold_id: str
    agent_id: str
    amount: float


class EnergyLedger:
    def __init__(self) -> None:
        self._balances: dict[str, float] = {}
        self._holds: dict[str, Hold] = {}

    def seed(self, agent_id: str, amount: float) -> None:
        self._balances[agent_id] = amount

    def balance_of(self, agent_id: str) -> float:
        return self._balances.get(agent_id, 0.0)

    def reserve(self, hold_id: str, agent_id: str, amount: float) -> Hold:
        if self.balance_of(agent_id) < amount:
            raise ValueError("insufficient core energy")
        self._balances[agent_id] -= amount
        hold = Hold(hold_id=hold_id, agent_id=agent_id, amount=amount)
        self._holds[hold_id] = hold
        return hold

    def capture(self, hold_id: str, amount: float) -> None:
        hold = self._holds.pop(hold_id)
        remainder = hold.amount - amount
        if remainder > 0:
            self._balances[hold.agent_id] = self.balance_of(hold.agent_id) + remainder

    def refund(self, hold_id: str, ratio: float = 1.0) -> None:
        hold = self._holds.pop(hold_id)
        self._balances[hold.agent_id] = self.balance_of(hold.agent_id) + hold.amount * ratio

    def transfer(self, sender: str, receiver: str, amount: float) -> None:
        if self.balance_of(sender) < amount:
            raise ValueError("insufficient funds")
        self._balances[sender] -= amount
        self.credit(receiver, amount)

    def credit(self, receiver: str, amount: float) -> None:
        self._balances[receiver] = self.balance_of(receiver) + amount
