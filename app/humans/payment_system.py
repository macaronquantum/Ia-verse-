from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Dict

from app.security.tamper_log import TamperEvidentLog


@dataclass
class Escrow:
    escrow_id: str
    amount: float
    released: bool = False


class CryptoPaymentSystem:
    """Crypto-native payment system (Coinbase Commerce + native settlement hooks)."""

    def __init__(self, api_key: str | None = None, api_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("COINBASE_COMMERCE_API_KEY", "")
        self.api_url = api_url or os.getenv("COINBASE_COMMERCE_API_URL", "https://api.commerce.coinbase.com")
        self.log = TamperEvidentLog()

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not self.api_key:
            raise ValueError("COINBASE_COMMERCE_API_KEY missing")
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.api_url}{path}",
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "X-CC-Api-Key": self.api_key,
                "X-CC-Version": "2018-03-22",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def create_payment_request(self, name: str, description: str, amount: float, currency: str = "USD") -> dict:
        payload = {"name": name, "description": description, "pricing_type": "fixed_price", "local_price": {"amount": f"{amount:.2f}", "currency": currency}}
        res = self._request("POST", "/charges", payload)
        self.log.append("payment_request_created", json.dumps(res.get("data", {})))
        return res

    def verify_payment(self, charge_id: str) -> bool:
        res = self._request("GET", f"/charges/{charge_id}")
        statuses = [t.get("status") for t in res.get("data", {}).get("timeline", [])]
        paid = any(s in {"COMPLETED", "CONFIRMED"} for s in statuses)
        self.log.append("payment_verified", f"{charge_id}:{paid}")
        return paid


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
