#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import secrets
print('NEW_GATEWAY_ENCRYPTION_KEY=' + secrets.token_hex(32))
PY
