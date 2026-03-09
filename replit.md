# IA-Verse Backend

## Overview
A FastAPI-based virtual world simulation backend (economic game). AI agents make decisions each tick, with companies, banks, loans, and markets.

## Architecture
- **Language**: Python 3.12
- **Framework**: FastAPI + Uvicorn
- **No database**: All state is in-memory via the `WorldEngine`
- **Port**: 5000

## Project Structure
- `app/main.py` — FastAPI app and REST endpoints
- `app/simulation.py` — Core `WorldEngine` simulation logic
- `app/agents/` — AI agent decision-making modules
- `app/economy/` — Market analysis and opportunity engine
- `app/business/` — Business provisioning engine
- `app/memory/` — Episodic memory and vector store
- `app/world/` — World state and crisis engine
- `app/social/` — Social network and messaging
- `app/marketplace/` — Marketplace engine
- `web/dashboard/` — Static HTML dashboard
- `tests/` — pytest test suite

## Running Locally
The workflow command is:
```
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
- `GET /health` — Health check
- `POST /worlds` — Create a new world
- `GET /worlds/{world_id}` — Get world state
- `POST /worlds/{world_id}/agents` — Create an AI agent
- `POST /worlds/{world_id}/companies` — Create a company
- `POST /worlds/{world_id}/tick` — Advance simulation N ticks
- `POST /worlds/{world_id}/bank/deposit` — Bank deposit
- `POST /worlds/{world_id}/bank/withdraw` — Bank withdrawal
- `POST /worlds/{world_id}/bank/loan` — Request a loan
- `POST /worlds/{world_id}/bank/repay` — Repay a loan

## Deployment
- Target: autoscale
- Run: `uvicorn app.main:app --host 0.0.0.0 --port 5000`
