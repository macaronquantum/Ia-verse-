from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.api.monitoring import router as monitoring_router
from pydantic import BaseModel, Field

from app.simulation import WorldEngine


app = FastAPI(title="IA-Verse Backend", version="1.0.0")
engine = WorldEngine()


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


app.include_router(monitoring_router)
