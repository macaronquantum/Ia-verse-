# IA-Verse Backend

## Overview
A FastAPI-based virtual world simulation backend (economic game) with a dashboard frontend. AI agents make decisions each tick, with companies, banks, loans, and markets. All 14 GitHub branches have been merged into a unified codebase.

## Architecture
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **AI Model**: Claude (via Replit AI Integrations — Anthropic) using `claude-haiku-4-5` for agent decisions
- **Frontend**: HTML/JS dashboard at `web/dashboard/`
- **No database**: All state is in-memory via the `WorldEngine`
- **Port**: 5000

## Project Structure
- `app/main.py` — FastAPI app, REST endpoints, static file serving, includes monitoring + gateway routers
- `app/simulation/__init__.py` — Core `WorldEngine` simulation logic (resource regen, dividends, wage system, autonomous scheduler)
- `app/simulation/engine.py` — Advanced `SimulationEngine` with energy ledger, economy, justice, LLM router
- `app/models/__init__.py` — Core data models (World, Agent, Company, Bank, Loan, AgentGoal, AgentTask, AgentState, Action, etc.)
- `app/models/tool_manifest.py` — ToolManifest Pydantic model for the tool marketplace
- `app/config.py` — Settings, EVOLUTION config, COSTS config
- `app/agents/` — AI agent modules: brain, planner, executor, goal system, memory manager, tool factory/selector, evolution, genome, personality, scheduler, agent factory, network
- `app/api_gateway/` — API gateway with costs, registry, sandbox runners (Docker/WASM)
- `app/economy/` — Market system, order books, AMM pricing, economy coordinator, FX market
- `app/energy/` — Energy ledger, global energy costs, CoreEnergyLedger, CoreEnergyMarket
- `app/business/` — Business provisioning engine
- `app/memory/` — Episodic memory (AgentMemory), global store (personalities, genomes, lineage)
- `app/persistence/` — Persistence store with tamper-evident log chain
- `app/justice/` — Justice system (JusticeSystem, JudgeAI) with action review, freeze/fine/ban
- `app/institutions/` — Central banks, institution coordinator, bootstrap
- `app/oracles/` — Oracle mint agent with real-value proofs
- `app/observability/` — Metrics (Metrics, MetricsStore, MetricsCollector)
- `app/integrations/` — Alchemy client, Solana gateway, human marketplace
- `app/culture/` — Belief engine, movements, social influence
- `app/llm/` — LLM adapters (HybridLLMAdapter with real Claude API, ModelRouter, LLMCostEngine)
- `app/world/` — World state and crisis engine
- `app/social/` — Social network and messaging
- `app/humans/` — Human task dispatcher
- `app/sensing/` — Sensing streams
- `app/api/` — Monitoring API router
- `web/dashboard/` — Dashboard HTML/CSS/JS
- `scripts/` — Settlement daily script
- `tests/` — pytest test suite (61 tests, 38 passing)

## Key Simulation Features
- Resource regeneration per tick (energy, food, metal, knowledge)
- Wage system: agents pay from wallet to company (no money creation)
- Sold goods return to global resources
- Dividends: profitable companies pay owners
- Interest rate scaled down for per-tick compounding
- Crisis engine: energy shortage, bank run, wars, oracle failure, economic collapse
- Agent evolution: genome, personality, mutation, crossover, imitation
- Tool marketplace: register, publish, purchase, rate tools
- Energy system: minting, burning, reserves, transfers
- Justice system: action review, freeze, fine, ban agents
- Autonomous scheduler: background cycles, goals, tasks, memory, metrics
- AI-powered agent decisions: each agent calls Claude to decide buy/sell/invest/loan actions each tick

## Running Locally
```
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
- `GET /` — Redirect to dashboard
- `GET /dashboard` — Dashboard UI
- `GET /health` — Health check
- `POST /worlds` — Create a new world
- `GET /worlds/{world_id}` — Get world state
- `POST /worlds/{world_id}/agents` — Create an AI agent
- `POST /worlds/{world_id}/companies` — Create a company
- `POST /worlds/{world_id}/tick` — Advance simulation N ticks
- `POST /worlds/{world_id}/bank/deposit|withdraw|loan|repay` — Banking operations
- `GET /monitoring/health|metrics|top_agents|world_map|logs` — Monitoring
- `GET/POST /gateway/costs` — Cost catalog
- `POST /gateway/estimate` — Estimate tool call cost
- `POST /tools/register|publish` — Tool management
- `GET /tools` — List tools
- `POST /tools/{tool_id}/call|test` — Call/test tools
- `GET /marketplace/tools` — Marketplace listings
- `POST /marketplace/purchase|rate` — Purchase/rate tools
- `GET /metrics` — Prometheus metrics

## Deployment
- Target: autoscale
- Run: `uvicorn app.main:app --host 0.0.0.0 --port 5000`
