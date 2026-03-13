from __future__ import annotations

import base64
import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from solders.keypair import Keypair


@dataclass
class WalletRecord:
    wallet_id: str
    agent_id: str
    network: str
    public_key: str
    encrypted_private_key: str
    nonce: str
    created_at: float


class WalletManager:
    """Production wallet manager with encrypted private-key at-rest storage."""

    def __init__(self, master_key: str | None = None) -> None:
        master_key = master_key or os.getenv("WALLET_MASTER_KEY", "")
        if not master_key:
            raise ValueError("WALLET_MASTER_KEY is required in production")
        self._key = hashlib.sha256(master_key.encode()).digest()
        self._records: dict[str, WalletRecord] = {}
        self._audit_log: list[dict[str, Any]] = []

    def _encrypt(self, private_key: str, aad: str) -> tuple[str, str]:
        nonce = os.urandom(12)
        encrypted = AESGCM(self._key).encrypt(nonce, private_key.encode(), aad.encode())
        return base64.b64encode(encrypted).decode(), base64.b64encode(nonce).decode()

    def _decrypt(self, encrypted_private_key: str, nonce: str, aad: str) -> str:
        return AESGCM(self._key).decrypt(
            base64.b64decode(nonce),
            base64.b64decode(encrypted_private_key),
            aad.encode(),
        ).decode()

    def _create_solana_wallet(self) -> tuple[str, str]:
        keypair = Keypair()
        return str(keypair.pubkey()), base64.b64encode(bytes(keypair)).decode()

    def create_wallet(self, agent_id: str, network: str = "solana") -> dict[str, str]:
        wallet_id = str(uuid4())
        if network.lower() != "solana":
            raise ValueError(f"unsupported network: {network}")

        public_key, private_key = self._create_solana_wallet()
        encrypted_private_key, nonce = self._encrypt(private_key, agent_id)
        self._records[wallet_id] = WalletRecord(
            wallet_id=wallet_id,
            agent_id=agent_id,
            network=network,
            public_key=public_key,
            encrypted_private_key=encrypted_private_key,
            nonce=nonce,
            created_at=time.time(),
        )
        return {"wallet_id": wallet_id, "public_key": public_key, "network": network}

    def list_wallets(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        out = []
        for rec in self._records.values():
            if agent_id and rec.agent_id != agent_id:
                continue
            out.append(
                {
                    "wallet_id": rec.wallet_id,
                    "agent_id": rec.agent_id,
                    "public_key": rec.public_key,
                    "network": rec.network,
                    "created_at": rec.created_at,
                }
            )
        return out

    def export_private_key(self, agent_id: str, wallet_id: str, request_password: str) -> str:
        if request_password != os.getenv("OPERATOR_PASSPHRASE", ""):
            raise PermissionError("invalid operator passphrase")
        rec = self._records.get(wallet_id)
        if not rec or rec.agent_id != agent_id:
            raise KeyError("wallet not found")

        private_key = self._decrypt(rec.encrypted_private_key, rec.nonce, agent_id)
        self._audit_log.append(
            {
                "event": "reveal_private_key",
                "agent_id": agent_id,
                "wallet_id": wallet_id,
                "ts": time.time(),
            }
        )
        return private_key

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return self._audit_log
