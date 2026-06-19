#!/bin/sh
# Gera /config.js em runtime a partir da env VITE_API_URL.
# O index.html carrega esse arquivo ANTES do bundle, então a aplicação lê
# window.__APP_CONFIG__.API_URL sem precisar de rebuild para mudar a URL.
set -e

: "${VITE_API_URL:=http://localhost:5001/predict}"

CONFIG_FILE="/usr/share/nginx/html/config.js"
cat > "$CONFIG_FILE" <<EOF
window.__APP_CONFIG__ = { API_URL: "${VITE_API_URL}" };
EOF

echo "[app-config] API_URL=${VITE_API_URL}"
