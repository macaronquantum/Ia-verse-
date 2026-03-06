#!/usr/bin/env bash
set -euo pipefail
docker compose -f docker-compose.dev.yml up -d postgres redis
python scripts/world_bootstrap.py
if command -v tmux >/dev/null; then
  tmux new-session -d -s ia_verse 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
  tmux split-window -t ia_verse 'python run_worker.py --tick-seconds ${TICK_SECONDS:-5}'
else
  ./scripts/run_simulation.sh "${TICK_SECONDS:-5}"
fi
