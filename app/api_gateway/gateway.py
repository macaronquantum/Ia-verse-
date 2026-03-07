from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class GatewayCall:
    service: str
    endpoint: str
    payload: Dict


@dataclass
class APIGateway:
    egress_whitelist: List[str] = field(default_factory=lambda: ["stub://"])
    calls: List[GatewayCall] = field(default_factory=list)

    def route(self, service: str, endpoint: str, payload: Dict) -> Dict:
        if not any(endpoint.startswith(prefix) for prefix in self.egress_whitelist):
            raise ValueError("egress endpoint not whitelisted")
        call = GatewayCall(service=service, endpoint=endpoint, payload=payload)
        self.calls.append(call)
        return {"ok": True, "service": service, "endpoint": endpoint, "payload": payload}
