#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from app.economy.opportunity_engine import OpportunityEngine
engine = OpportunityEngine()
ops = engine.get_opportunities('seed-agent', 48, {'tool_shortages':['crm-automation'],'human_demand':1})
print(f'Seeded opportunities: {len(ops)}')
PY
