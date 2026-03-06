#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cat <<'EOF'
Optional local LLM:
- Ollama: https://ollama.com/download
- or vLLM: pip install vllm
EOF
cp -n .env.example .env || true
