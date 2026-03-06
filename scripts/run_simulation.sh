#!/usr/bin/env bash
set -euo pipefail
TICK_SECONDS="${1:-5}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
python run_worker.py --tick-seconds "$TICK_SECONDS" &
wait
