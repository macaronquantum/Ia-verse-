from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.config import settings
from app.integrations.solana_gateway import Transfer, batch_settlement, create_wallet as sol_create_wallet
from app.persistence.store import store
from app.tools.alchemy_tool import fetch_crypto_quote


@dataclass
class ServiceEntry:
    name: str
    cost: float
    quota_per_day: int


SERVICE_REGISTRY = {
    "alchemy": ServiceEntry("alchemy", cost=0.5, quota_per_day=1000),
    "exchange_stub": ServiceEntry("exchange_stub", cost=0.8, quota_per_day=200),
}


def _charge(agent_id: str, amount: float) -> None:
    q = store.quotas.setdefault(agent_id, {"used": 0, "quota": 500, "spent": 0.0})
    if q["used"] >= q["quota"]:
        raise ValueError("quota exceeded")
    q["used"] += 1
    q["spent"] += amount


def create_wallet(agent_id: str, network: str = "solana") -> dict:
    if network != "solana":
        raise ValueError("unsupported network")
    _charge(agent_id, 0.02)
    return sol_create_wallet(f"agent:{agent_id}")


def transfer_funds(agent_id: str, from_pubkey: str, to_pubkey: str, asset: str, amount: float) -> dict:
    _charge(agent_id, 0.01)
    return batch_settlement([Transfer(from_pubkey=from_pubkey, to_pubkey=to_pubkey, asset=asset, amount=amount)])


def place_order(agent_id: str, market: str, order_spec: dict) -> dict:
    _charge(agent_id, 0.05)
    oid = str(uuid.uuid4())
    store.transactions.append({"kind": "order", "agent_id": agent_id, "market": market, "order_spec": order_spec, "order_id": oid})
    return {"order_id": oid, "status": "accepted"}


def call_third_party(agent_id: str, service_name: str, payload: dict) -> dict:
    service = SERVICE_REGISTRY[service_name]
    _charge(agent_id, service.cost)
    if service_name == "alchemy":
        return fetch_crypto_quote(payload.get("symbol", "SOL"))
    return {"service": service_name, "payload": payload, "status": "stubbed"}


def request_llm(agent_id: str, model: str, prompt: str, budget_tokens: int) -> dict:
    cost = settings.COST_LLMS.get(model, 1.0)
    _charge(agent_id, cost)
    return {"model": model, "prompt_tokens": min(len(prompt.split()), budget_tokens), "result": "stub-response"}


def create_tool(agent_id: str, manifest: dict, code_stub: str) -> dict:
    _charge(agent_id, 0.2)
    tid = str(uuid.uuid4())
    store.organizations[tid] = {"type": "tool", "manifest": manifest, "code_stub": code_stub, "owner": agent_id}
    return {"tool_id": tid, "status": "sandboxed_registered"}
