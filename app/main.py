from __future__ import annotations

import asyncio
import random
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.api.monitoring import router as monitoring_router
from app.api_gateway.gateway import gateway_router
from app.models import COUNTRY_COORDS, COUNTRIES, Resource
from app.simulation import WorldEngine


app = FastAPI(title="IA-Verse Backend", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(monitoring_router)
app.include_router(gateway_router)
engine = WorldEngine()

_auto_sim_task: Optional[asyncio.Task] = None
_auto_sim_speed: float = 5.0  # seconds between ticks
_auto_sim_running: bool = False
_auto_sim_stopped: bool = False
_active_world_id: Optional[str] = None

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "dashboard"
DASHBOARD_PAGE = STATIC_DIR / "index.html"


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_PAGE)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CreateWorldRequest(BaseModel):
    name: str = Field(min_length=1)


class CreateAgentRequest(BaseModel):
    name: str = Field(min_length=1)


class CreateCompanyRequest(BaseModel):
    owner_agent_id: str
    name: str = Field(min_length=1)


class TickRequest(BaseModel):
    steps: int = Field(default=1, ge=1, le=1000)


class MoneyRequest(BaseModel):
    owner_id: str
    amount: float = Field(gt=0)


class RepayRequest(BaseModel):
    owner_id: str
    loan_id: str
    amount: float = Field(gt=0)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/worlds")
def create_world(payload: CreateWorldRequest) -> dict:
    world = engine.create_world(payload.name)
    return engine.snapshot(world.id)


@app.get("/worlds/{world_id}")
def get_world(world_id: str) -> dict:
    try:
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/agents")
def create_agent(world_id: str, payload: CreateAgentRequest) -> dict:
    try:
        engine.create_agent(world_id, payload.name)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/companies")
def create_company(world_id: str, payload: CreateCompanyRequest) -> dict:
    try:
        engine.create_company(world_id, payload.owner_agent_id, payload.name)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/tick")
def tick(world_id: str, payload: TickRequest) -> dict:
    try:
        engine.tick(world_id, payload.steps)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/bank/deposit")
def deposit(world_id: str, payload: MoneyRequest) -> dict:
    try:
        engine.transfer_wallet_to_bank(world_id, payload.owner_id, payload.amount)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/bank/withdraw")
def withdraw(world_id: str, payload: MoneyRequest) -> dict:
    try:
        engine.transfer_bank_to_wallet(world_id, payload.owner_id, payload.amount)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/bank/loan")
def loan(world_id: str, payload: MoneyRequest) -> dict:
    try:
        loan_id = engine.request_loan(world_id, payload.owner_id, payload.amount)
        snapshot = engine.snapshot(world_id)
        snapshot["last_loan_id"] = loan_id
        return snapshot
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/worlds/{world_id}/bank/repay")
def repay(world_id: str, payload: RepayRequest) -> dict:
    try:
        engine.repay_loan(world_id, payload.owner_id, payload.loan_id, payload.amount)
        return engine.snapshot(world_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/simulation/state")
def get_simulation_state() -> dict:
    global _active_world_id
    if _auto_sim_stopped or not engine.worlds:
        return {"active": False, "world": None}
    if _active_world_id and _active_world_id in engine.worlds:
        wid = _active_world_id
    else:
        wid = list(engine.worlds.keys())[-1]
        _active_world_id = wid
    world = engine.worlds[wid]
    agents_list = []
    for a in world.agents.values():
        coords = COUNTRY_COORDS.get(a.country, (0, 0))
        jitter_seed = hash(a.id) % 1000
        lat_jitter = (jitter_seed / 1000 - 0.5) * 4
        lng_jitter = ((jitter_seed * 7) % 1000 / 1000 - 0.5) * 4
        total_assets = a.wallet + sum(a.inventory.get(r, 0) * world.market_prices.get(r, 0) for r in Resource)
        agents_list.append({
            "id": a.id, "name": a.name, "type": a.agent_type, "wallet": round(a.wallet, 2),
            "total_assets": round(total_assets, 2), "country": a.country,
            "lat": coords[0] + lat_jitter, "lng": coords[1] + lng_jitter,
            "influence": a.influence_score, "risk": a.risk_score,
            "personality": a.personality, "has_company": a.company_id is not None,
            "inventory": {k.value: round(v, 1) for k, v in a.inventory.items()},
        })
    companies_list = []
    for c in world.companies.values():
        owner = world.agents.get(c.owner_agent_id)
        companies_list.append({
            "id": c.id, "name": c.name, "owner": owner.name if owner else "unknown",
            "cash": round(c.cash, 2), "productivity": round(c.productivity, 2),
        })
    ai_events = [e for e in world.event_log if "[AI]" in e]
    return {
        "active": True,
        "running": _auto_sim_running,
        "speed": _auto_sim_speed,
        "world_id": wid,
        "world_name": world.name,
        "tick": world.tick_count,
        "agents": agents_list,
        "companies": companies_list,
        "market_prices": {k.value: v for k, v in world.market_prices.items()},
        "global_resources": {k.value: round(v, 1) for k, v in world.global_resources.items()},
        "bank": {"reserve": round(world.bank.reserve, 2), "loans": len(world.bank.loans), "accounts": len(world.bank.accounts)},
        "events": world.event_log[-50:],
        "ai_events": ai_events[-30:],
    }


@app.get("/api/agents")
def get_all_agents() -> dict:
    global _active_world_id
    if not engine.worlds:
        return {"agents": []}
    wid = _active_world_id or list(engine.worlds.keys())[-1]
    world = engine.worlds.get(wid)
    if not world:
        return {"agents": []}
    agents = []
    for a in world.agents.values():
        coords = COUNTRY_COORDS.get(a.country, (0, 0))
        total_assets = a.wallet + sum(a.inventory.get(r, 0) * world.market_prices.get(r, 0) for r in Resource)
        agents.append({
            "id": a.id, "name": a.name, "type": a.agent_type, "wallet": round(a.wallet, 2),
            "total_assets": round(total_assets, 2), "country": a.country,
            "lat": coords[0], "lng": coords[1],
            "influence": a.influence_score, "risk": a.risk_score,
            "personality": a.personality, "has_company": a.company_id is not None,
            "company_id": a.company_id,
            "inventory": {k.value: round(v, 1) for k, v in a.inventory.items()},
            "wealth_history": a.wealth_history[-50:],
            "decision_log": a.decision_log[-20:],
        })
    return {"agents": agents, "tick": world.tick_count}


@app.get("/api/agents/{agent_id}")
def get_agent_profile(agent_id: str) -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid:
        raise HTTPException(404, "no world")
    world = engine.worlds.get(wid)
    if not world:
        raise HTTPException(404, "world not found")
    agent = world.agents.get(agent_id)
    if not agent:
        raise HTTPException(404, "agent not found")
    coords = COUNTRY_COORDS.get(agent.country, (0, 0))
    total_assets = agent.wallet + sum(agent.inventory.get(r, 0) * world.market_prices.get(r, 0) for r in Resource)
    company = world.companies.get(agent.company_id) if agent.company_id else None
    return {
        "id": agent.id, "name": agent.name, "type": agent.agent_type,
        "wallet": round(agent.wallet, 2), "total_assets": round(total_assets, 2),
        "country": agent.country, "lat": coords[0], "lng": coords[1],
        "influence": agent.influence_score, "risk": agent.risk_score,
        "personality": agent.personality,
        "inventory": {k.value: round(v, 1) for k, v in agent.inventory.items()},
        "wealth_history": agent.wealth_history,
        "decision_log": agent.decision_log,
        "company": {"id": company.id, "name": company.name, "cash": round(company.cash, 2), "productivity": round(company.productivity, 2)} if company else None,
        "bank_balance": round(world.bank.accounts.get(agent.id, type("", (), {"balance": 0})).balance, 2),
    }


@app.get("/api/economy")
def get_economy() -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid or wid not in engine.worlds:
        return {"active": False}
    world = engine.worlds[wid]
    wallets = [a.wallet for a in world.agents.values()]
    total_money = sum(wallets) + sum(c.cash for c in world.companies.values()) + world.bank.reserve
    total_energy = world.global_resources.get(Resource.ENERGY, 0) + sum(a.inventory.get(Resource.ENERGY, 0) for a in world.agents.values())
    sorted_agents = sorted(world.agents.values(), key=lambda a: a.wallet, reverse=True)
    gini = 0.0
    if wallets and len(wallets) > 1:
        sorted_w = sorted(wallets)
        n = len(sorted_w)
        cum = sum((2 * i - n + 1) * w for i, w in enumerate(sorted_w))
        mean = sum(sorted_w) / n
        if mean > 0:
            gini = round(cum / (n * n * mean), 3)
    bankrupt = sum(1 for a in world.agents.values() if a.wallet < 1)
    top_agents = [{"name": a.name, "type": a.agent_type, "wallet": round(a.wallet, 2), "country": a.country, "id": a.id} for a in sorted_agents[:10]]
    return {
        "active": True,
        "tick": world.tick_count,
        "total_money_supply": round(total_money, 2),
        "total_energy": round(total_energy, 2),
        "agent_count": len(world.agents),
        "company_count": len(world.companies),
        "bankrupt_agents": bankrupt,
        "gini_index": gini,
        "bank_reserve": round(world.bank.reserve, 2),
        "total_loans": len(world.bank.loans),
        "market_prices": {k.value: round(v, 2) for k, v in world.market_prices.items()},
        "top_agents": top_agents,
        "global_resources": {k.value: round(v, 1) for k, v in world.global_resources.items()},
    }


@app.get("/api/events/feed")
def get_events_feed() -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid or wid not in engine.worlds:
        return {"headlines": [], "tick": 0}
    world = engine.worlds[wid]
    headlines = []
    for e in world.event_log[-20:]:
        text = e
        if "[AI]" in text:
            parts = text.split("[AI]", 1)
            text = parts[1].strip() if len(parts) > 1 else text
            paren_idx = text.find("(")
            if paren_idx > 0:
                text = text[:paren_idx].strip()
        headlines.append(text)
    return {"headlines": headlines[-15:], "tick": world.tick_count}


class SimControlRequest(BaseModel):
    action: str
    speed: Optional[float] = None
    agent_name: Optional[str] = None
    world_name: Optional[str] = None
    agent_count: Optional[int] = None


async def _auto_simulation_loop():
    global _auto_sim_running, _active_world_id
    while _auto_sim_running:
        try:
            if _active_world_id and _active_world_id in engine.worlds:
                engine.tick(_active_world_id, 1)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Auto-sim tick failed: {e}")
        await asyncio.sleep(_auto_sim_speed)


@app.post("/api/simulation/control")
async def simulation_control(payload: SimControlRequest) -> dict:
    global _auto_sim_task, _auto_sim_speed, _auto_sim_running, _auto_sim_stopped, _active_world_id

    if payload.action == "create_world":
        _auto_sim_running = False
        _auto_sim_stopped = False
        if _auto_sim_task:
            _auto_sim_task.cancel()
            _auto_sim_task = None
        name = payload.world_name or f"World-{len(engine.worlds) + 1}"
        world = engine.create_world(name)
        _active_world_id = world.id
        central_banks = [
            ("Federal Reserve", "United States"), ("European Central Bank", "Germany"),
            ("Bank of Japan", "Japan"), ("Bank of England", "United Kingdom"),
            ("People's Bank of China", "China"),
        ]
        commercial_banks = [
            ("JPMorgan Chase", "United States"), ("Goldman Sachs", "United States"),
            ("HSBC", "United Kingdom"), ("Deutsche Bank", "Germany"),
            ("BNP Paribas", "France"), ("UBS", "Switzerland"),
            ("Barclays", "United Kingdom"), ("Credit Suisse", "Switzerland"),
            ("Santander", "Spain"), ("ING Group", "Netherlands"),
            ("Mitsubishi UFJ", "Japan"), ("ICBC", "China"),
            ("Bank of Brazil", "Brazil"), ("Royal Bank of Canada", "Canada"),
            ("ANZ Bank", "Australia"), ("Standard Chartered", "Singapore"),
            ("Citibank", "United States"), ("Morgan Stanley", "United States"),
            ("DBS Bank", "Singapore"), ("Nordea", "Sweden"),
        ]
        companies = [
            ("TechCorp Global", "United States"), ("EnergyMax", "Saudi Arabia"),
            ("FoodGlobal Inc", "Brazil"), ("MetalWorks Ltd", "Australia"),
            ("KnowledgeHub", "India"), ("DataStream", "South Korea"),
            ("AutoDrive", "Germany"), ("PharmaLife", "Switzerland"),
            ("AeroSpace One", "France"), ("OceanTrade", "Singapore"),
            ("MineralCo", "South Africa"), ("AgriTech", "Argentina"),
            ("SolarPower", "Spain"), ("ChipDesign", "Taiwan"),
            ("FinanceAI", "United Kingdom"), ("LogiChain", "Netherlands"),
            ("CloudNet", "Ireland"), ("BioGen", "Denmark"),
            ("RoboCorp", "Japan"), ("GreenEnergy", "Norway"),
        ]
        states = [
            ("State of USA", "United States"), ("State of China", "China"),
            ("State of Germany", "Germany"), ("State of Japan", "Japan"),
            ("State of India", "India"), ("State of Brazil", "Brazil"),
            ("State of UK", "United Kingdom"), ("State of France", "France"),
            ("State of Russia", "Russia"), ("State of Australia", "Australia"),
        ]
        judges = [
            ("Judge Alpha", "United States"), ("Judge Europa", "Belgium"),
            ("Judge Asia", "Singapore"), ("Judge Africa", "South Africa"),
            ("Judge Latam", "Brazil"),
        ]
        energy_provider = [("World Energy Authority", "UAE")]
        citizens = [
            (f"Citizen {c}", c) for c in random.sample(list(COUNTRY_COORDS.keys()), min(40, len(COUNTRY_COORDS)))
        ]
        all_agents = []
        for name_c, country in central_banks:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "central_bank"
            a.wallet = 10000.0
            all_agents.append(a)
        for name_c, country in commercial_banks:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "bank"
            a.wallet = 1000.0
            all_agents.append(a)
        for name_c, country in companies:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "company"
            a.wallet = 500.0
            all_agents.append(a)
        for name_c, country in states:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "state"
            a.wallet = 5000.0
            all_agents.append(a)
        for name_c, country in judges:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "judge"
            a.wallet = 200.0
            all_agents.append(a)
        for name_c, country in energy_provider:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "energy_provider"
            a.wallet = 50000.0
            all_agents.append(a)
        for name_c, country in citizens:
            a = engine.create_agent(world.id, name_c)
            a.country = country
            a.agent_type = "citizen"
            all_agents.append(a)
        return {"status": "ok", "world_id": world.id, "agents": len(all_agents)}

    if payload.action == "start":
        _auto_sim_stopped = False
        if not _active_world_id:
            raise HTTPException(400, "no world created")
        if _auto_sim_running and _auto_sim_task and not _auto_sim_task.done():
            return {"status": "already_running", "speed": _auto_sim_speed}
        _auto_sim_running = True
        _auto_sim_speed = payload.speed or _auto_sim_speed
        _auto_sim_task = asyncio.create_task(_auto_simulation_loop())
        return {"status": "running", "speed": _auto_sim_speed}

    if payload.action == "pause":
        _auto_sim_running = False
        if _auto_sim_task:
            _auto_sim_task.cancel()
            _auto_sim_task = None
        return {"status": "paused"}

    if payload.action == "stop":
        _auto_sim_running = False
        _auto_sim_stopped = True
        if _auto_sim_task:
            _auto_sim_task.cancel()
            _auto_sim_task = None
        return {"status": "stopped"}

    if payload.action == "speed":
        _auto_sim_speed = max(1.0, payload.speed or 5.0)
        return {"status": "ok", "speed": _auto_sim_speed}

    if payload.action == "tick":
        if _active_world_id and _active_world_id in engine.worlds:
            engine.tick(_active_world_id, 1)
            return {"status": "ok", "tick": engine.worlds[_active_world_id].tick_count}
        return {"status": "error", "message": "no active world"}

    if payload.action == "spawn_agent":
        if not _active_world_id:
            return {"status": "error", "message": "no world"}
        name = payload.agent_name or f"Agent-{random.randint(1000, 9999)}"
        engine.create_agent(_active_world_id, name)
        return {"status": "ok", "name": name}

    raise HTTPException(400, f"unknown action: {payload.action}")
