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
import hashlib
from app.models import COUNTRY_COORDS, COUNTRIES, SYSTEM_CURRENCIES
from app.simulation import WorldEngine


app = FastAPI(title="IA-Verse Backend", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(monitoring_router)
app.include_router(gateway_router)
engine = WorldEngine()

_auto_sim_task: Optional[asyncio.Task] = None
_auto_sim_speed: float = 5.0
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


CB_CURRENCIES = {
    "Federal Reserve": "USC",
    "European Central Bank": "EUC",
    "Bank of Japan": "JPC",
    "Bank of England": "GBC",
    "People's Bank of China": "CNC",
}

CB_COUNTRIES = {
    "Federal Reserve": "United States",
    "European Central Bank": "Germany",
    "Bank of Japan": "Japan",
    "Bank of England": "United Kingdom",
    "People's Bank of China": "China",
}


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
    ledger = engine.get_ledger(wid)
    agents_list = []
    for a in world.agents.values():
        coords = COUNTRY_COORDS.get(a.country, (0, 0))
        jitter_seed = hash(a.id) % 1000
        lat_jitter = (jitter_seed / 1000 - 0.5) * 4
        lng_jitter = ((jitter_seed * 7) % 1000 / 1000 - 0.5) * 4
        energy = ledger.balance_of(a.id)
        agents_list.append({
            "id": a.id, "name": a.name, "type": a.agent_type, "wallet": round(a.wallet, 2),
            "core_energy": round(energy, 2),
            "total_value": round(a.wallet + energy * world.energy_price, 2),
            "currency": a.currency,
            "country": a.country,
            "lat": coords[0] + lat_jitter, "lng": coords[1] + lng_jitter,
            "influence": a.influence_score, "risk": a.risk_score,
            "personality": a.personality, "ideology": a.ideology,
            "has_company": a.company_id is not None,
            "alive": a.alive,
        })
    companies_list = []
    for c in world.companies.values():
        owner = world.agents.get(c.owner_agent_id)
        companies_list.append({
            "id": c.id, "name": c.name, "owner": owner.name if owner else "unknown",
            "cash": round(c.cash, 2), "productivity": round(c.productivity, 2),
            "revenue": round(c.revenue, 2),
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
        "energy_price": world.energy_price,
        "total_energy_supply": round(world.total_energy_supply, 1),
        "total_energy_burned": round(world.total_energy_burned, 1),
        "currencies": world.currencies,
        "bank": {
            "reserve": round(world.bank.reserve, 2),
            "loans": len(world.bank.loans),
            "accounts": len(world.bank.accounts),
            "interest_rate": world.bank.base_interest_rate,
        },
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
    ledger = engine.get_ledger(wid)
    agents = []
    for a in world.agents.values():
        coords = COUNTRY_COORDS.get(a.country, (0, 0))
        energy = ledger.balance_of(a.id)
        agents.append({
            "id": a.id, "name": a.name, "type": a.agent_type, "wallet": round(a.wallet, 2),
            "core_energy": round(energy, 2),
            "total_value": round(a.wallet + energy * world.energy_price, 2),
            "currency": a.currency, "country": a.country,
            "lat": coords[0], "lng": coords[1],
            "influence": a.influence_score, "risk": a.risk_score,
            "personality": a.personality, "ideology": a.ideology,
            "has_company": a.company_id is not None,
            "company_id": a.company_id,
            "alive": a.alive,
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
    ledger = engine.get_ledger(wid)
    coords = COUNTRY_COORDS.get(agent.country, (0, 0))
    energy = ledger.balance_of(agent.id)
    company = world.companies.get(agent.company_id) if agent.company_id else None
    return {
        "id": agent.id, "name": agent.name, "type": agent.agent_type,
        "wallet": round(agent.wallet, 2),
        "core_energy": round(energy, 2),
        "total_value": round(agent.wallet + energy * world.energy_price, 2),
        "currency": agent.currency,
        "country": agent.country, "lat": coords[0], "lng": coords[1],
        "influence": agent.influence_score, "risk": agent.risk_score,
        "personality": agent.personality, "ideology": agent.ideology,
        "alive": agent.alive,
        "wealth_history": agent.wealth_history,
        "decision_log": agent.decision_log,
        "company": {"id": company.id, "name": company.name, "cash": round(company.cash, 2), "productivity": round(company.productivity, 2)} if company else None,
        "bank_balance": round(world.bank.accounts.get(agent.id, type("", (), {"balance": 0})).balance, 2),
        "loans": [{
            "id": l.id,
            "principal": round(l.amount, 2),
            "interest_rate": l.interest_rate,
            "remaining": round(l.remaining, 2),
        } for l in world.bank.get_loans(agent.id)],
        "transactions": [tx.to_dict() for tx in world.transactions
                         if tx.from_id == agent.id or tx.to_id == agent.id][-50:],
    }


def _generate_wallet_keys(agent_id: str) -> dict:
    seed = hashlib.sha256(agent_id.encode()).hexdigest()
    private_key = "0x" + hashlib.sha256(("pk_" + seed).encode()).hexdigest()
    public_address = "0x" + hashlib.sha256(("addr_" + seed).encode()).hexdigest()[:40]
    return {"private_key": private_key, "public_address": public_address}


@app.get("/api/wallets")
def get_wallets() -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid or wid not in engine.worlds:
        return {"wallets": []}
    world = engine.worlds[wid]
    ledger = engine.get_ledger(wid)
    wallets = []
    for a in world.agents.values():
        energy = ledger.balance_of(a.id)
        keys = _generate_wallet_keys(a.id)
        bank_acct = world.bank.accounts.get(a.id)
        wallets.append({
            "id": a.id,
            "name": a.name,
            "type": a.agent_type,
            "currency": a.currency,
            "wallet_balance": round(a.wallet, 2),
            "bank_balance": round(bank_acct.balance, 2) if bank_acct else 0.0,
            "core_energy": round(energy, 2),
            "total_value": round(a.wallet + energy * world.energy_price, 2),
            "alive": a.alive,
            "private_key": keys["private_key"],
            "public_address": keys["public_address"],
        })
    wallets.sort(key=lambda w: w["total_value"], reverse=True)
    return {"wallets": wallets, "tick": world.tick_count}


@app.get("/api/transactions")
def get_transactions(agent_id: str = None, tx_type: str = None, limit: int = 200) -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid or wid not in engine.worlds:
        return {"transactions": [], "tick": 0}
    world = engine.worlds[wid]
    txs = world.transactions
    if agent_id:
        txs = [tx for tx in txs if tx.from_id == agent_id or tx.to_id == agent_id]
    if tx_type:
        txs = [tx for tx in txs if tx.tx_type == tx_type]
    filtered_total = len(txs)
    result = [tx.to_dict() for tx in txs[-limit:]]
    result.reverse()
    return {"transactions": result, "tick": world.tick_count,
            "total_count": filtered_total}


@app.get("/api/economy")
def get_economy() -> dict:
    global _active_world_id
    wid = _active_world_id or (list(engine.worlds.keys())[-1] if engine.worlds else None)
    if not wid or wid not in engine.worlds:
        return {"active": False}
    world = engine.worlds[wid]
    ledger = engine.get_ledger(wid)
    values = [a.wallet + ledger.balance_of(a.id) * world.energy_price for a in world.agents.values()]
    total_money = sum(a.wallet for a in world.agents.values()) + sum(c.cash for c in world.companies.values()) + world.bank.reserve
    total_energy = sum(ledger.balance_of(a.id) for a in world.agents.values())
    sorted_agents = sorted(world.agents.values(), key=lambda a: a.wallet + ledger.balance_of(a.id) * world.energy_price, reverse=True)
    gini = 0.0
    if values and len(values) > 1:
        sorted_w = sorted(values)
        n = len(sorted_w)
        cum = sum((2 * i - n + 1) * w for i, w in enumerate(sorted_w))
        mean = sum(sorted_w) / n
        if mean > 0:
            gini = round(cum / (n * n * mean), 3)
    dead_agents = sum(1 for a in world.agents.values() if not a.alive)
    top_agents = [{
        "name": a.name, "type": a.agent_type,
        "wallet": round(a.wallet, 2),
        "core_energy": round(ledger.balance_of(a.id), 2),
        "total_value": round(a.wallet + ledger.balance_of(a.id) * world.energy_price, 2),
        "country": a.country, "id": a.id,
    } for a in sorted_agents[:10]]
    return {
        "active": True,
        "tick": world.tick_count,
        "total_money_supply": round(total_money, 2),
        "total_energy": round(total_energy, 2),
        "total_energy_burned": round(world.total_energy_burned, 2),
        "energy_price": world.energy_price,
        "agent_count": len(world.agents),
        "alive_agents": sum(1 for a in world.agents.values() if a.alive),
        "dead_agents": dead_agents,
        "company_count": len(world.companies),
        "gini_index": gini,
        "bank_reserve": round(world.bank.reserve, 2),
        "interest_rate": world.bank.base_interest_rate,
        "total_loans": len(world.bank.loans),
        "currencies": world.currencies,
        "top_agents": top_agents,
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
        ledger = engine.get_ledger(world.id)

        central_banks = [
            ("Federal Reserve", "United States", "USC", 500.0),
            ("European Central Bank", "Germany", "EUC", 500.0),
            ("Bank of Japan", "Japan", "JPC", 500.0),
            ("Bank of England", "United Kingdom", "GBC", 500.0),
            ("People's Bank of China", "China", "CNC", 500.0),
        ]
        commercial_banks = [
            ("JPMorgan Chase", "United States", "USC"), ("Goldman Sachs", "United States", "USC"),
            ("HSBC", "United Kingdom", "GBC"), ("Deutsche Bank", "Germany", "EUC"),
            ("BNP Paribas", "France", "EUC"), ("UBS", "Switzerland", "EUC"),
            ("Barclays", "United Kingdom", "GBC"), ("Credit Suisse", "Switzerland", "EUC"),
            ("Santander", "Spain", "EUC"), ("ING Group", "Netherlands", "EUC"),
            ("Mitsubishi UFJ", "Japan", "JPC"), ("ICBC", "China", "CNC"),
            ("Bank of Brazil", "Brazil", "USC"), ("Royal Bank of Canada", "Canada", "USC"),
            ("ANZ Bank", "Australia", "GBC"), ("Standard Chartered", "Singapore", "GBC"),
            ("Citibank", "United States", "USC"), ("Morgan Stanley", "United States", "USC"),
            ("DBS Bank", "Singapore", "GBC"), ("Nordea", "Sweden", "EUC"),
        ]
        companies = [
            ("TechCorp Global", "United States", "USC"), ("EnergyMax", "Saudi Arabia", "USC"),
            ("FoodGlobal Inc", "Brazil", "USC"), ("MetalWorks Ltd", "Australia", "GBC"),
            ("KnowledgeHub", "India", "GBC"), ("DataStream", "South Korea", "JPC"),
            ("AutoDrive", "Germany", "EUC"), ("PharmaLife", "Switzerland", "EUC"),
            ("AeroSpace One", "France", "EUC"), ("OceanTrade", "Singapore", "GBC"),
            ("MineralCo", "South Africa", "GBC"), ("AgriTech", "Argentina", "USC"),
            ("SolarPower", "Spain", "EUC"), ("ChipDesign", "Taiwan", "CNC"),
            ("FinanceAI", "United Kingdom", "GBC"), ("LogiChain", "Netherlands", "EUC"),
            ("CloudNet", "Ireland", "EUC"), ("BioGen", "Denmark", "EUC"),
            ("RoboCorp", "Japan", "JPC"), ("GreenEnergy", "Norway", "EUC"),
        ]
        states = [
            ("State of USA", "United States", "USC"), ("State of China", "China", "CNC"),
            ("State of Germany", "Germany", "EUC"), ("State of Japan", "Japan", "JPC"),
            ("State of India", "India", "GBC"), ("State of Brazil", "Brazil", "USC"),
            ("State of UK", "United Kingdom", "GBC"), ("State of France", "France", "EUC"),
            ("State of Russia", "Russia", "EUC"), ("State of Australia", "Australia", "GBC"),
        ]
        judges = [
            ("Judge Alpha", "United States", "USC"), ("Judge Europa", "Belgium", "EUC"),
            ("Judge Asia", "Singapore", "GBC"), ("Judge Africa", "South Africa", "GBC"),
            ("Judge Latam", "Brazil", "USC"),
        ]
        energy_authority = [("EnergyCore Authority", "UAE", "USC")]

        currency_for_country = {}
        for _, country, ccy, *_ in central_banks:
            currency_for_country[country] = ccy
        for _, country, ccy in commercial_banks + companies + states + judges + energy_authority:
            currency_for_country[country] = ccy

        all_agents = []

        for name_c, country, currency, energy_reserve in central_banks:
            a = engine.create_agent(world.id, name_c, core_energy=energy_reserve)
            a.country = country
            a.agent_type = "central_bank"
            a.currency = currency
            a.wallet = 10000.0
            a.ideology = "bureaucrat"
            all_agents.append(a)

        for name_c, country, currency in commercial_banks:
            a = engine.create_agent(world.id, name_c, core_energy=50.0)
            a.country = country
            a.agent_type = "bank"
            a.currency = currency
            a.wallet = 1000.0
            a.ideology = "capitalist"
            all_agents.append(a)

        for name_c, country, currency in companies:
            a = engine.create_agent(world.id, name_c, core_energy=30.0)
            a.country = country
            a.agent_type = "company"
            a.currency = currency
            a.wallet = 500.0
            all_agents.append(a)

        for name_c, country, currency in states:
            a = engine.create_agent(world.id, name_c, core_energy=100.0)
            a.country = country
            a.agent_type = "state"
            a.currency = currency
            a.wallet = 5000.0
            a.ideology = "bureaucrat"
            all_agents.append(a)

        for name_c, country, currency in judges:
            a = engine.create_agent(world.id, name_c, core_energy=20.0)
            a.country = country
            a.agent_type = "judge"
            a.currency = currency
            a.wallet = 200.0
            all_agents.append(a)

        for name_c, country, currency in energy_authority:
            a = engine.create_agent(world.id, name_c, core_energy=5000.0)
            a.country = country
            a.agent_type = "energy_provider"
            a.currency = currency
            a.wallet = 50000.0
            a.ideology = "cooperative"
            all_agents.append(a)

        citizen_countries = random.sample(list(COUNTRY_COORDS.keys()), min(60, len(COUNTRY_COORDS)))
        currency_zones = {
            "USC": ["United States", "Canada", "Mexico", "Brazil", "Argentina", "Colombia", "Chile", "Peru",
                     "Venezuela", "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Guatemala", "Cuba",
                     "Dominican Republic", "Honduras", "Costa Rica", "Panama", "Jamaica", "Trinidad",
                     "Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman", "Iran", "Iraq"],
            "EUC": ["Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Sweden", "Norway",
                     "Denmark", "Finland", "Poland", "Austria", "Switzerland", "Ireland", "Portugal",
                     "Czech Republic", "Greece", "Romania", "Hungary", "Ukraine", "Turkey", "Russia",
                     "Morocco", "Algeria", "Tunisia", "Libya", "Nigeria", "Ghana", "Cameroon", "Senegal",
                     "Ivory Coast", "Iceland", "Luxembourg", "Malta", "Cyprus", "Estonia", "Latvia",
                     "Lithuania", "Slovakia", "Slovenia", "Croatia", "Serbia", "Bulgaria"],
            "GBC": ["United Kingdom", "India", "Australia", "New Zealand", "South Africa", "Kenya",
                     "Ethiopia", "Tanzania", "Uganda", "Mozambique", "Angola", "DR Congo", "Zimbabwe",
                     "Rwanda", "Zambia", "Singapore", "Malaysia", "Israel", "Jordan", "Lebanon", "Egypt",
                     "Georgia", "Azerbaijan"],
            "JPC": ["Japan", "South Korea", "Thailand", "Vietnam", "Philippines", "Indonesia", "Myanmar",
                     "Cambodia", "Sri Lanka", "Nepal", "Taiwan", "Mongolia"],
            "CNC": ["China", "Bangladesh", "Pakistan", "Kazakhstan", "Uzbekistan"],
        }
        country_to_currency = {}
        for ccy, countries_list in currency_zones.items():
            for c in countries_list:
                country_to_currency[c] = ccy

        for country in citizen_countries:
            a = engine.create_agent(world.id, f"Citizen {country}", core_energy=5.0)
            a.country = country
            a.agent_type = "citizen"
            a.currency = country_to_currency.get(country, "USC")
            a.wallet = 100.0
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
