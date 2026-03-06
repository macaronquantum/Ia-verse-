# LA-VERSE Autonomous Economic Simulation

This backend models a continuously running AI civilization where agents consume **Core Energy** to reason and act.

## Architecture

- `app/agents/`: agent base classes and tier-aware factories.
- `app/economy/`: FX, equity, and policy-rate mechanics.
- `app/institutions/`: central banks, states, and banks.
- `app/energy/`: core energy ledger, mint oracle, and conversion market.
- `app/justice/`: transparent Judge AI rulings.
- `app/api_gateway/`: sandboxed external-action permission layer.
- `app/llm/`: model adapters and tier-based routing.
- `app/simulation/`: asynchronous tick engine and world orchestration.

## Core Mechanics Implemented

- Genesis Core Energy supply is `10,000` units distributed across 5 continental central banks.
- Agent tiers with differentiated LLM model selection and energy consumption.
- Tick engine (`SimulationEngine`) that asynchronously performs observation, decision, action processing, and world updates.
- Core Energy burn and internal currency->energy conversion.
- Basic monetary policy, FX trading, and primary/secondary equity structures.
- Judge system with explainable rulings and penalty recommendations.
- API gateway with permission controls and audit logs.

## Run

```bash
python -m app.main
```

## Test

```bash
pytest -q
```
