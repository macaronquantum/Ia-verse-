# IA-Verse Backend

## Overview
A FastAPI-based virtual world simulation backend (economic game) with a premium futuristic dashboard frontend. Claude AI agents make real decisions each tick, with companies, banks, loans, and markets. All 14 GitHub branches have been merged into a unified codebase.

## Architecture
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **AI Model**: Claude (via Replit AI Integrations — Anthropic) using `claude-haiku-4-5` for agent decisions
- **Frontend**: Premium glassmorphism SPA with 3D globe (Three.js), agent explorer, economy dashboard, live AI feed, simulation controls
- **No database**: All state is in-memory via the `WorldEngine`
- **Port**: 5000

## Project Structure
- `app/main.py` — FastAPI app, REST endpoints, dashboard API, static file serving, auto-simulation loop
- `app/simulation/__init__.py` — Core `WorldEngine` simulation logic (resource regen, dividends, wage system, autonomous scheduler, AI agent decisions)
- `app/simulation/engine.py` — Advanced `SimulationEngine` with energy ledger, economy, justice, LLM router
- `app/models/__init__.py` — Core data models (World, Agent, Company, Bank, Loan, AgentGoal, AgentTask, AgentState, Action, etc.) with enriched Agent fields (type, country, influence, risk, personality, wealth_history, decision_log)
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
- `web/dashboard/index.html` — Dashboard SPA shell with glassmorphism nav, 4 views
- `web/dashboard/style.css` — Full glassmorphism/liquid glass styling with animations
- `web/dashboard/app.js` — Complete dashboard JS: globe (Three.js), agent explorer, economy, controls, live feed, auto-polling
- `scripts/` — Settlement daily script
- `tests/` — pytest test suite (61 tests, 38 passing)

## Dashboard Features
- **3D Globe View**: Three.js globe with agents as glowing 3D objects (cubes for banks, spheres for others), drag rotation, zoom, hover tooltips, star field
- **Agent Explorer**: Searchable/filterable/sortable agent list, click for profile with wealth chart, inventory, decision log
- **Economy Dashboard**: Money supply, Gini index, resource bars, market prices, leaderboard
- **Simulation Controls**: Create world, start/pause auto-sim, speed slider, manual tick, spawn agents
- **Live AI Feed**: Real-time Claude AI decision events with color-coded entries
- **Auto-polling**: State refreshes every 4 seconds

## Dashboard API Endpoints
- `GET /api/simulation/state` — Full world state (agents, companies, prices, events)
- `GET /api/agents` — All agents with enriched data
- `GET /api/agents/{id}` — Agent profile with history
- `GET /api/economy` — Economy metrics (money supply, Gini, leaderboard)
- `POST /api/simulation/control` — Actions: create_world, start, pause, speed, tick, spawn_agent

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
- Agent enrichment: type, country, influence score, risk score, personality, wealth history, decision log

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
