from __future__ import annotations

from app.integrations.base import BaseClient


class AlchemyClient(BaseClient):
    def get_token_price(self, symbol: str) -> dict:
        if self.dev_mode:
            return {"symbol": symbol, "price_usd": 123.45, "source": "simulated"}
        return {"symbol": symbol, "price_usd": 0.0, "source": "live-not-configured"}

    def lookup_transaction(self, tx_hash: str) -> dict:
        return {"tx_hash": tx_hash, "status": "confirmed" if self.dev_mode else "unknown"}
