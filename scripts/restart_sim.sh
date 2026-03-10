#!/usr/bin/env bash
set -euo pipefail
if command -v tmux >/dev/null && tmux has-session -t ia_verse 2>/dev/null; then
  tmux kill-session -t ia_verse
fi
./scripts/run_all.sh
