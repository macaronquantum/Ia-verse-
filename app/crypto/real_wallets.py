from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.fernet import Fernet

from app.config import settings


@dataclass
class EncryptedWallet:
    chain: str
    address: str
    encrypted_private_key: str


class RealWalletManager:
    def __init__(self, secret: str | None = None) -> None:
        digest = hashlib.sha256((secret or settings.WALLET_KEY).encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt_private_key(self, private_key: str) -> str:
        return self._fernet.encrypt(private_key.encode()).decode()

    def decrypt_private_key(self, encrypted_key: str) -> str:
        return self._fernet.decrypt(encrypted_key.encode()).decode()

    def create_wallet(self, chain: str, address: str, private_key: str) -> EncryptedWallet:
        return EncryptedWallet(chain=chain, address=address, encrypted_private_key=self.encrypt_private_key(private_key))

    def check_balance(self, chain: str, address: str) -> dict:
        return {"chain": chain, "address": address, "balance": 0.0, "status": "stubbed"}

    def send_tokens(self, chain: str, from_key: str, to_address: str, amount: float) -> dict:
        return {"chain": chain, "to": to_address, "amount": amount, "tx_hash": "pending", "status": "queued"}
