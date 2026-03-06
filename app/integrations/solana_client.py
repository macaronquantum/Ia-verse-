from __future__ import annotations

from app.integrations.base import BaseClient


class SolanaClient(BaseClient):
    def create_wallet(self) -> dict:
        return {"wallet": "solana_wallet_simulated"}

    def verify_transaction(self, signature: str) -> dict:
        return {"signature": signature, "verified": True}
