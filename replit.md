# IA-Verse

## Overview
An AI multi-agent economic system where Claude AI agents make real economic decisions each tick. EnergyCore represents real computational cost — agents must acquire EnergyCore to reason, act, and survive. Central banks create their own currencies backed by EnergyCore. Agents seek investment, generate revenue, and manage banking relationships. Built with FastAPI + Leaflet.js dashboard.

## Architecture
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **AI Model**: Claude (via Replit AI Integrations — Anthropic) using `claude-haiku-4-5` for agent decisions
- **Frontend**: Light-theme glassmorphism SPA with Leaflet.js flat planisphere map, agent explorer, economy dashboard, live AI feed, simulation controls
- **No database**: All state is in-memory via the `WorldEngine`
- **Port**: 5000

## Core Economic Principles
- **EnergyCore**: The fundamental resource representing real computational capacity. Agents burn EnergyCore for AI reasoning, actions, and maintenance. If EnergyCore reaches 0, the agent dies.
- **System Currencies**: 5 currencies backed by EnergyCore, each created by a central bank:
  - USC (United States Credit) — Federal Reserve
  - EUC (European Credit) — ECB
  - JPC (Japan-Pacific Credit) — Bank of Japan
  - GBC (British Credit) — Bank of England
  - CNC (China Network Credit) — People's Bank of China
- **Banking**: Commercial banks lend capital, manage deposits, charge interest
- **Agent Actions**: request_investment, acquire_energy, generate_revenue, deposit, withdraw, take_loan, create_company, hire_worker, set_interest_rate, inject_liquidity, web_search, idle
- **Web Search**: Agents can search the real web (DuckDuckGo) for market data, news, economic trends. Costs 0.5 EnergyCore per search, 2-tick cooldown. Results stored per agent and fed into future decision context.

## Project Structure
- `app/main.py` — FastAPI app, REST endpoints, dashboard API, world bootstrap, auto-simulation loop
- `app/simulation/__init__.py` — Core `WorldEngine` with EnergyCore-based economics, AI agent decisions, energy ledger integration
- `app/simulation/engine.py` — Advanced `SimulationEngine` with energy ledger, economy, justice, LLM router
- `app/models/__init__.py` — Core data models (World, Agent, Company, Bank, Loan) with EnergyCore fields, system currencies
- `app/config.py` — Settings, EVOLUTION config, COSTS config
- `app/energy/core.py` — EnergyLedger (mint/burn/transfer/charge), CoreEnergyLedger, GlobalEnergyCosts
- `app/web_search.py` — WebSearchEngine using DuckDuckGo (ddgs), per-agent search history, cooldown, knowledge context
- `app/agents/` — Personality system, genome/DNA, evolution, mutation, imitation, mind/cognition, beliefs
- `app/llm/adapters.py` — HybridLLMAdapter with Claude API, ModelRouter, LLMCostEngine
- `app/economy/` — Market system, economy coordinator, FX market
- `app/institutions/` — Central banks, institution coordinator
- `app/justice/` — Justice system (JudgeAI) with action review
- `app/culture/` — Belief engine, movements, social influence
- `app/social/` — Social network and messaging
- `web/dashboard/` — Dashboard frontend (index.html, style.css, app.js)

## World Bootstrap (create_world)
- 5 central banks with own currencies + 500 EnergyCore each + 10K currency
- 20 commercial banks with 50 EnergyCore + 1K currency
- 20 companies with 30 EnergyCore + 500 currency
- 10 states with 100 EnergyCore + 5K currency
- 5 judges with 20 EnergyCore + 200 currency
- 1 EnergyCore Authority with 5000 EnergyCore + 50K currency
- 60 citizens across 100 countries with 5 EnergyCore + 100 currency
- AI tick limit: 10 agents per tick (random subset) for performance
- Total: ~121 agents

## Dashboard Features (5 Views)
- **Map View**: Leaflet.js planisphere, agent markers with type-based colors and size proportional to value, live event feed
- **Agent Explorer**: Search/filter/sort by type, currency, EnergyCore, influence. Tabbed agent profile (Overview with wealth chart, Transactions, Loans with terms, Actions/decision log, Web Research). Fade animation on agent switch
- **Wallets View**: Table of all agent wallets with currency balance, bank balance, EnergyCore, simulated public address and private key (click to reveal)
- **Transactions View**: Chronological expandable transaction cards with type badges (color-coded), from/to agents, amounts. Click to expand for full details (loan terms, energy prices, etc.). Filter by type and agent
- **Economy Dashboard**: Money supply, total EnergyCore, energy burned, Gini index, alive/dead agents, bank reserve, currencies, leaderboard
- **Simulation Controls**: Create World button + Run/Stop toggle (green Run / red Stop)
- **Live Feed**: Real-time economic events from /api/events/feed
- **Auto-polling**: State refreshes every 4 seconds
- **Design**: Light theme, glassmorphism, Inter font, responsive (desktop/tablet/mobile)

## API Endpoints
- `GET /api/simulation/state` — Current world state with all agents
- `POST /api/simulation/control` — Actions: create_world, start, stop, tick
- `GET /api/agents` — List all agents
- `GET /api/agents/{id}` — Agent detail with loans and transactions
- `GET /api/wallets` — All agent wallets with simulated keys
- `GET /api/transactions` — Structured transactions (filters: agent_id, type, limit)
- `GET /api/economy` — Economy metrics and leaderboard
- `GET /api/events/feed` — Live event feed

## Transaction Types
deposit, withdraw, loan_issued, loan_repaid, acquire_energy, energy_burn, revenue, labor_income, dividend, company_create, investment, liquidity_injection, interest_rate_change, web_search

## Running
```
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```
