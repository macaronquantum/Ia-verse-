from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.security.tamper_log import TamperEvidentLog


@dataclass
class Escrow:
    escrow_id: str
    amount: float
    released: bool = False


class PaymentSystem:
    def __init__(self) -> None:
        self.escrows: Dict[str, Escrow] = {}
        self.log = TamperEvidentLog()

    def hold(self, escrow_id: str, amount: float) -> Escrow:
        e = Escrow(escrow_id=escrow_id, amount=amount)
        self.escrows[escrow_id] = e
        self.log.append("hire_escrow", f"{escrow_id}:{amount}")
        return e

    def release(self, escrow_id: str) -> Escrow:
        e = self.escrows[escrow_id]
        e.released = True
        self.log.append("hire_release", escrow_id)
        return e
