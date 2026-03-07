#!/usr/bin/env bash
set -euo pipefail
echo "Stub runner: start uvicorn and background worker stack (Celery/RQ integration point)."
uvicorn app.main:app --host 0.0.0.0 --port 8000
