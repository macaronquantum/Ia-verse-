from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Dict
from uuid import uuid4

from app.config import settings
from app.energy.core import CoreEnergyLedger
from app.persistence.store import store


@dataclass
class RealValueProof:
    agent_id: str
    external_reference: str
    amount: float
    signature: str


class MintOracleAgent:
    _instance: "MintOracleAgent | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ledger: CoreEnergyLedger) -> None:
        self.ledger = ledger
        self.audit_log: list[str] = []

    def verify_real_value_proof(self, proof: RealValueProof) -> bool:
        expected = sha256(f"{proof.agent_id}:{proof.external_reference}:{proof.amount}".encode()).hexdigest()
        is_valid = proof.signature == expected and proof.amount > 0
        self.audit_log.append(f"verify:{proof.agent_id}:{is_valid}")
        return is_valid

    def mint_on_verified_value(self, proof: RealValueProof) -> float:
        if not self.verify_real_value_proof(proof):
            raise ValueError("real value proof rejected")
        self.ledger.credit(proof.agent_id, proof.amount)
        self.audit_log.append(f"mint:{proof.agent_id}:{proof.amount}")
        return proof.amount


class OracleRegistry:
    def __init__(self) -> None:
        self.mint_oracle_id: str | None = None
        self.oracles: Dict[str, str] = {}

    def register_mint_oracle(self, oracle_id: str) -> None:
        if self.mint_oracle_id and self.mint_oracle_id != oracle_id:
            raise ValueError("only one MintOracleAgent is allowed")
        self.mint_oracle_id = oracle_id


_default_oracle = MintOracleAgent(CoreEnergyLedger())
_pending: dict[str, RealValueProof] = {}


def submit_proof(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], RealValueProof):
        return _default_oracle.mint_on_verified_value(args[0])

    agent_id, wallet, external_reference, meta = args
    usd = float((meta or {}).get("usd_value", 0.0))
    amount = max(0.0, usd / 1_000_000)
    signature = sha256(f"{wallet}:{external_reference}:{amount}".encode()).hexdigest()
    proof = RealValueProof(agent_id=wallet, external_reference=external_reference, amount=amount, signature=signature)
    request_id = str(uuid4())
    _pending[request_id] = proof
    return {"request_id": request_id, "status": "submitted", "agent_id": agent_id}


def verify_proof(proof_or_request):
    if isinstance(proof_or_request, RealValueProof):
        return _default_oracle.verify_real_value_proof(proof_or_request)

    proof = _pending.pop(proof_or_request)
    if not getattr(settings, "DEV_ALLOW_MINT", False):
        return {"status": "rejected", "reason": "mint_disabled"}
    _default_oracle.mint_on_verified_value(proof)
    store.core_energy_ledger[proof.agent_id] = store.core_energy_ledger.get(proof.agent_id, 0.0) + proof.amount
    return {"status": "minted", "amount": proof.amount, "wallet": proof.agent_id}
