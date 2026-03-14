#!/bin/sh
set -eu

API_URL_VALUE="${API_URL:-http://localhost:8000}"
cat > /usr/share/nginx/html/config.js <<EOF
window.__APP_CONFIG__ = {
  API_URL: "${API_URL_VALUE}"
};
EOF

echo "Frontend: http://SERVER_IP:3000"
echo "API docs: http://SERVER_IP:8000/docs"

exec nginx -g 'daemon off;'
