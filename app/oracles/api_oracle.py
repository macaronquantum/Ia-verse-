from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Dict

from app.energy.core import CoreEnergyLedger


@dataclass
class RealValueProof:
    agent_id: str
    external_reference: str
    amount: float
    signature: str


class MintOracleAgent:
    """Oracle minter unique. Isolation/sécurité représentées par API stricte.

    Un seul agent de mint doit exister dans le système.
    """

    _instance: "MintOracleAgent | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ledger: CoreEnergyLedger) -> None:
        self.ledger = ledger
        self.audit_log: list[str] = []

    def verify_real_value_proof(self, proof: RealValueProof) -> bool:
        """Stub sécurisé: on ne branche pas de flux d'argent réel direct.

        Le check est volontairement minimal et auditable en attendant des audits
        externes / intégration custodial.
        """
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
