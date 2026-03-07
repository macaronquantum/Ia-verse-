# Autonomous Startup Layer

This document describes the autonomous startup creation engine:
- Opportunity detection (`app/economy/opportunity_engine.py`)
- Business provisioning (`app/business/engine.py`)
- Tool publication and marketplace monetization
- Human labor integration with judge-controlled spend
- Tamper-evident billing logs and reserve/refund policies

## Dev mode
Set `DEV_MODE=1` (default) to use stubbed connectors. Security policies and judge checks still run.

## Run
- `python -m pytest -q`
- `bash scripts/bootstrap_opportunities.sh`
- `bash scripts/run_agents_workers.sh`
