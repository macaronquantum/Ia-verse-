from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


class EnergyError(Exception):
    pass


@dataclass(slots=True)
class GlobalEnergyCosts:
    local_reasoning_tick: float = 0.001
    spawn_subjudge: float = 2.0
    llm_external_base: dict[str, float] = field(default_factory=lambda: {
        "openai": 0.05,
        "anthropic": 0.06,
        "google": 0.04,
    })


GLOBAL_ENERGY_COSTS = GlobalEnergyCosts()


class CoreEnergyLedger:
    def __init__(self) -> None:
        self.balances: dict[str, float] = defaultdict(float)

    def credit(self, account_id: str, amount: float) -> None:
        self.balances[account_id] += amount

    def debit(self, account_id: str, amount: float) -> None:
        if self.balances[account_id] < amount:
            raise EnergyError(f"insufficient balance for {account_id}")
        self.balances[account_id] -= amount

    def burn(self, account_id: str, amount: float) -> None:
        if self.balances[account_id] < amount:
            raise EnergyError(f"insufficient balance for {account_id}")
        self.balances[account_id] -= amount


class CoreEnergyMarket:
    def __init__(self, rate: float = 1.0) -> None:
        self._rate = rate

    def quote(self, currency: str, amount: float) -> float:
        return amount * self._rate


@dataclass(slots=True)
class EnergyConfig:
    base_action_cost: float = 0.5
    local_reasoning_cost: float = 0.8
    external_reasoning_cost: float = 3.0
    maintenance_cost: float = 0.2
    agent_creation_cost: float = 10.0


class EnergyLedger:
    """Tracks all energy balance updates and transfers."""

    def __init__(self, config: EnergyConfig | None = None) -> None:
        self.config = config or EnergyConfig()
        self._balances: dict[str, float] = defaultdict(float)
        self._total_burned = 0.0

    def balance_of(self, account_id: str) -> float:
        return self._balances[account_id]

    def mint(self, account_id: str, amount: float) -> None:
        self._balances[account_id] += amount

    def burn(self, account_id: str, amount: float, *, allow_negative: bool = False) -> None:
        if not allow_negative and self._balances[account_id] < amount:
            raise EnergyError(f"insufficient funds for {account_id}: {self._balances[account_id]} < {amount}")
        self._balances[account_id] -= amount
        self._total_burned += amount

    def transfer(self, sender_id: str, receiver_id: str, amount: float) -> None:
        if amount <= 0:
            raise EnergyError("transfer amount must be positive")
        self.burn(sender_id, amount)
        self.mint(receiver_id, amount)

    def charge_action(self, agent_id: str) -> None:
        self.burn(agent_id, self.config.base_action_cost)

    def charge_reasoning(self, agent_id: str, *, external: bool) -> None:
        amount = self.config.external_reasoning_cost if external else self.config.local_reasoning_cost
        self.burn(agent_id, amount)

    def charge_maintenance(self, agent_id: str) -> None:
        self.burn(agent_id, self.config.maintenance_cost)

    def charge_creation(self, agent_id: str) -> None:
        self.burn(agent_id, self.config.agent_creation_cost)

    def seed(self, account_id: str, amount: float) -> None:
        self._balances[account_id] += amount

    def reserve(self, hold_id: str, account_id: str, amount: float) -> None:
        if self._balances[account_id] < amount:
            raise ValueError(f"insufficient energy for {account_id}")
        self._balances[account_id] -= amount
        self._balances[f"hold:{hold_id}"] = amount

    def capture(self, hold_id: str, amount: float) -> None:
        key = f"hold:{hold_id}"
        held = self._balances.pop(key, 0.0)
        self._total_burned += min(held, amount)

    def credit(self, account_id: str, amount: float) -> None:
        self._balances[account_id] += amount

    def refund(self, hold_id: str, ratio: float = 1.0) -> None:
        key = f"hold:{hold_id}"
        held = self._balances.pop(key, 0.0)
        refund_amount = held * ratio
        self._total_burned += held - refund_amount

    def distribution(self) -> dict[str, float]:
        return dict(self._balances)

    @property
    def total_burned(self) -> float:
        return self._total_burned
