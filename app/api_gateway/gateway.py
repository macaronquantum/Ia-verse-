from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, WebSocket
from pydantic import BaseModel, Field

from app.api_gateway.costs import CostCatalog, CostUpdate
from app.api_gateway.registry import Registry, marketplace_fee, role_allowed
from app.api_gateway.sandbox.docker_runner import DockerRunner
from app.api_gateway.sandbox.wasm_runner import WasmRunner
from app.energy.core import EnergyLedger
from app.integrations.alchemy_client import AlchemyClient
from app.models.tool_manifest import ToolManifest
from app.observability.metrics import MetricsStore


gateway_router = APIRouter(prefix="", tags=["api-gateway"])
registry = Registry()
cost_catalog = CostCatalog()
ledger = EnergyLedger()
ledger.seed("agent-alpha", 1000)
ledger.seed("agent-beta", 1000)
ledger.seed("treasury", 0)
runner = DockerRunner()
wasm_runner = WasmRunner()
metrics = MetricsStore()
quotas: dict[tuple[str, str], deque[float]] = defaultdict(deque)
reputation: dict[str, float] = defaultdict(lambda: 100.0)


class RegisterToolRequest(BaseModel):
    manifest: dict[str, Any]


class PublishToolRequest(BaseModel):
    signature: str


class ToolCallRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class EstimateRequest(BaseModel):
    tool_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ServiceRegisterRequest(BaseModel):
    service_id: str
    config: dict[str, Any]


class PurchaseRequest(BaseModel):
    tool_id: str
    model: str = "per_call"
    amount: float = 0.0


class RateRequest(BaseModel):
    tool_id: str
    score: int = Field(ge=1, le=5)
    review: str = ""


def _auth(agent_id: str | None, role: str | None) -> tuple[str, str]:
    if not agent_id:
        raise HTTPException(status_code=401, detail="missing x-agent-id")
    return agent_id, role or "citizen"


def _check_quota(agent_id: str, tool_id: str) -> None:
    key = (agent_id, tool_id)
    now = time.time()
    q = quotas[key]
    while q and (now - q[0]) > 60:
        q.popleft()
    if len(q) >= 30:
        reputation[agent_id] -= 5
        raise HTTPException(status_code=429, detail="quota exceeded")
    q.append(now)


def _estimate_cost(manifest: ToolManifest, duration_hint: float = 1.0) -> float:
    base = cost_catalog.get("tool_call_base") + manifest.cost_core_energy
    deps = sum(cost_catalog.get(f"{d.service_id}_price_query", 0.02) for d in manifest.external_dependencies)
    sandbox = cost_catalog.get("tool_sandbox_second") * duration_hint
    rep_factor = 1.0
    return (base + deps + sandbox) * rep_factor


@gateway_router.get("/gateway/costs")
def get_costs() -> dict[str, float]:
    return cost_catalog.all()


@gateway_router.post("/gateway/costs")
def update_costs(payload: CostUpdate, x_role: str | None = Header(default=None)) -> dict[str, Any]:
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="admin required")
    cost_catalog.update(payload.key, payload.value)
    return {"status": "ok", "costs": cost_catalog.all()}


@gateway_router.post("/gateway/estimate")
def estimate(payload: EstimateRequest) -> dict[str, Any]:
    record = registry.get_tool(payload.tool_id)
    return {"estimated_cost": _estimate_cost(record.manifest)}


@gateway_router.post("/tools/register")
def register_tool(
    payload: RegisterToolRequest,
    x_agent_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> dict[str, str]:
    agent_id, _ = _auth(x_agent_id, x_role)
    payload.manifest["creator_agent_id"] = agent_id
    manifest = registry.register_tool(payload.manifest)
    return {"tool_id": str(manifest.id)}


@gateway_router.post("/tools/publish")
def publish_tool(
    tool_id: str,
    payload: PublishToolRequest,
    x_agent_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> dict[str, str]:
    agent_id, _ = _auth(x_agent_id, x_role)
    record = registry.get_tool(tool_id)
    if record.manifest.creator_agent_id != agent_id:
        raise HTTPException(status_code=403, detail="creator required")
    registry.publish_tool(tool_id, payload.signature)
    return {"status": "published", "tool_id": tool_id}


@gateway_router.get("/tools")
def list_tools(tag: str | None = None, price: float | None = None) -> list[dict[str, Any]]:
    return [m.model_dump(mode="json") for m in registry.list_tools(tag=tag, max_price=price)]


@gateway_router.get("/tools/{tool_id}")
def get_tool(tool_id: str) -> dict[str, Any]:
    return registry.get_tool(tool_id).manifest.model_dump(mode="json")


@gateway_router.post("/tools/{tool_id}/test")
def test_tool(tool_id: str, payload: ToolCallRequest) -> dict[str, Any]:
    manifest = registry.get_tool(tool_id).manifest
    selected_runner = wasm_runner if manifest.entrypoint.endswith(".wasm") else runner
    return selected_runner.run(manifest, payload.payload, exec_options={"billing": False})


@gateway_router.post("/tools/{tool_id}/call")
def call_tool(
    tool_id: str,
    payload: ToolCallRequest,
    x_agent_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> dict[str, Any]:
    agent_id, role = _auth(x_agent_id, x_role)
    record = registry.get_tool(tool_id)
    manifest = record.manifest
    if not role_allowed(manifest, role, agent_id):
        raise HTTPException(status_code=403, detail="caller not allowed")
    _check_quota(agent_id, tool_id)

    estimated = _estimate_cost(manifest, payload.payload.get("simulate_duration", 1.0))
    risk = max(0.0, (100 - reputation[agent_id]) / 100)
    estimated *= 1 + risk
    hold_id = str(uuid4())
    try:
        ledger.reserve(hold_id, agent_id, estimated)
    except ValueError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    start = time.time()
    selected_runner = wasm_runner if manifest.entrypoint.endswith(".wasm") else runner
    result = selected_runner.run(manifest, payload.payload, exec_options={"agent_id": agent_id})
    duration = time.time() - start

    if result["status"] == "success":
        ledger.capture(hold_id, estimated)
        platform_fee = marketplace_fee(estimated)
        creator_cut = estimated - platform_fee
        ledger.credit(record.manifest.creator_agent_id, creator_cut)
        ledger.credit("treasury", platform_fee)
        record.revenue += creator_cut
        log = registry.log_usage(
            tool_id=tool_id,
            caller_agent_id=agent_id,
            status="success",
            cost=estimated,
            output=result.get("output"),
        )
        metrics.mark_call(tool_id, duration, estimated, ok=True)
        return {"status": "success", "output": result["output"], "cost": estimated, "usage_log_hash": log.hash}

    ledger.refund(hold_id, ratio=1.0)
    registry.log_usage(tool_id=tool_id, caller_agent_id=agent_id, status=result["status"], cost=0.0, output=None)
    metrics.mark_call(tool_id, duration, 0.0, ok=False)
    raise HTTPException(status_code=500, detail=result["status"])


@gateway_router.post("/services/register")
def register_service(payload: ServiceRegisterRequest, x_role: str | None = Header(default=None)) -> dict[str, str]:
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="admin required")
    registry.register_service(payload.service_id, payload.config)
    return {"status": "ok"}


@gateway_router.get("/services")
def list_services() -> dict[str, Any]:
    return registry.services


@gateway_router.get("/marketplace/tools")
def marketplace_tools() -> list[dict[str, Any]]:
    return registry.marketplace_tools()


@gateway_router.post("/marketplace/purchase")
def marketplace_purchase(payload: PurchaseRequest, x_agent_id: str | None = Header(default=None)) -> dict[str, Any]:
    agent_id, _ = _auth(x_agent_id, None)
    p = registry.purchase(payload.tool_id, agent_id, payload.model, payload.amount)
    return {"tool_id": p.tool_id, "agent_id": p.agent_id, "status": "purchased"}


@gateway_router.post("/marketplace/rate")
def marketplace_rate(payload: RateRequest, x_agent_id: str | None = Header(default=None)) -> dict[str, Any]:
    agent_id, _ = _auth(x_agent_id, None)
    rating = registry.add_rating(payload.tool_id, agent_id, payload.score, payload.review)
    return {"tool_id": rating.tool_id, "score": rating.score}


@gateway_router.get("/metrics")
def metrics_endpoint() -> str:
    return metrics.prometheus_text()


@gateway_router.websocket("/gateway/events")
async def events(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_json({"event": "connected", "message": "gateway event stream"})
    await ws.close()


@gateway_router.get("/integrations/alchemy/price")
def alchemy_price(symbol: str) -> dict[str, Any]:
    return AlchemyClient().get_token_price(symbol)
