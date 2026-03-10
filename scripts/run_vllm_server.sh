#!/usr/bin/env bash
set -euo pipefail
MODEL_NAME=${1:-mistral-7b}
MODEL_PATH=${2:-/var/models/${MODEL_NAME}}
python -m vllm.entrypoints.openai.api_server --model "$MODEL_PATH" --host 0.0.0.0 --port 8001
