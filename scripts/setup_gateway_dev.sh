#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
mkdir -p .data
cp -n .env.example .env || true
echo "[setup] gateway dev ready"
