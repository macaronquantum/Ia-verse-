from __future__ import annotations

from app.integrations.base import BaseClient


class StripeClient(BaseClient):
    def create_charge(self, amount: float, currency: str = "usd") -> dict:
        return {"charge_id": "ch_simulated", "amount": amount, "currency": currency, "status": "succeeded"}

    def webhook(self, event: dict) -> dict:
        return {"received": True, "type": event.get("type", "unknown")}
