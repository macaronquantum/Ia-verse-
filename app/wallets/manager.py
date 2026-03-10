from __future__ import annotations

import base64
import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:
    AESGCM = None


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
    def __init__(self, master_key: str | None = None) -> None:
        master_key = master_key or os.getenv("WALLET_MASTER_KEY", "dev-master-key-change-me")
        self._key = hashlib.sha256(master_key.encode()).digest()
        self._records: dict[str, WalletRecord] = {}
        self._audit_log: list[dict[str, Any]] = []

    def create_wallet(self, agent_id: str, network: str = "solana") -> dict[str, str]:
        wallet_id = str(uuid4())
        private_key = f"priv_{uuid4().hex}{uuid4().hex}"
        public_key = f"pub_{hashlib.sha256(private_key.encode()).hexdigest()[:32]}"
        nonce = os.urandom(12)
        if AESGCM:
            aes = AESGCM(self._key)
            encrypted = aes.encrypt(nonce, private_key.encode(), agent_id.encode())
        else:
            encrypted = bytes([b ^ self._key[i % len(self._key)] for i, b in enumerate(private_key.encode())])
        self._records[wallet_id] = WalletRecord(
            wallet_id=wallet_id,
            agent_id=agent_id,
            network=network,
            public_key=public_key,
            encrypted_private_key=base64.b64encode(encrypted).decode(),
            nonce=base64.b64encode(nonce).decode(),
            created_at=time.time(),
        )
        return {"wallet_id": wallet_id, "public_key": public_key, "network": network}

    def list_wallets(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        out = []
        for rec in self._records.values():
            if agent_id and rec.agent_id != agent_id:
                continue
            out.append({"wallet_id": rec.wallet_id, "agent_id": rec.agent_id, "public_key": rec.public_key, "network": rec.network, "balance": 0.0})
        return out

    def export_private_key(self, agent_id: str, wallet_id: str, request_password: str) -> str:
        if request_password != os.getenv("OPERATOR_PASSPHRASE", "operator-passphrase"):
            raise PermissionError("invalid operator passphrase")
        rec = self._records.get(wallet_id)
        if not rec or rec.agent_id != agent_id:
            raise KeyError("wallet not found")
        if AESGCM:
            aes = AESGCM(self._key)
            private_key = aes.decrypt(
                base64.b64decode(rec.nonce),
                base64.b64decode(rec.encrypted_private_key),
                agent_id.encode(),
            ).decode()
        else:
            raw = base64.b64decode(rec.encrypted_private_key)
            private_key = bytes([b ^ self._key[i % len(self._key)] for i, b in enumerate(raw)]).decode()
        self._audit_log.append({"event": "reveal_private_key", "agent_id": agent_id, "wallet_id": wallet_id, "ts": time.time()})
        return private_key

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return self._audit_log
