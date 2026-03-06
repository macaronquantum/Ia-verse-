from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
from uuid import uuid4


@dataclass
class GatewayPolicy:
    max_calls_per_agent: int = 50
    allowed_services: set[str] = field(default_factory=lambda: {"exchange", "weather", "compute", "solana"})


class APIGateway:
    def __init__(self, policy: GatewayPolicy | None = None) -> None:
        self.policy = policy or GatewayPolicy()
        self.call_count: Dict[str, int] = {}

    def _check_quota(self, agent_id: str) -> None:
        self.call_count[agent_id] = self.call_count.get(agent_id, 0) + 1
        if self.call_count[agent_id] > self.policy.max_calls_per_agent:
            raise ValueError("quota exceeded")

    def create_wallet(self, agent_id: str, network: str = "solana") -> Dict[str, str]:
        self._check_quota(agent_id)
        if network != "solana":
            raise ValueError("only solana is currently supported")
        return {"network": network, "address": f"So1-{uuid4().hex[:24]}", "pubkey": uuid4().hex}

    def place_order_on_exchange(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._check_quota(agent_id)
        return {"status": "accepted", "exchange_ref": uuid4().hex, "payload": payload}

    def call_external_api(self, agent_id: str, service: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._check_quota(agent_id)
        if service not in self.policy.allowed_services:
            raise ValueError("service not allowed")
        return {"service": service, "ok": True, "payload": payload}

    def run_job(self, agent_id: str, server_spec: Dict[str, Any]) -> Dict[str, Any]:
        self._check_quota(agent_id)
        return {"job_id": uuid4().hex, "status": "queued", "server_spec": server_spec}
