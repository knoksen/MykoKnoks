#!/usr/bin/env bash
set -euo pipefail

APP_NAME="mykoknoks"
PUBLIC_HOST="knoksen.nova.usbx.me"
BASE_PATH="/mykoknoks-api"
PORT="${1:-}"

PORTS_OUTPUT=""
if command -v app-ports >/dev/null 2>&1; then
  PORTS_OUTPUT="$(app-ports free 2>&1 || true)"

  if [[ -z "$PORT" ]]; then
    PORT="$(printf '%s\n' "$PORTS_OUTPUT" | grep -oE '[0-9]{5}' | head -n 1 || true)"
    if [[ -n "$PORT" ]]; then
      echo "Auto-selected Ultra assigned port: $PORT"
    fi
  fi

  if [[ -z "$PORT" ]]; then
    echo "ERROR: no free assigned Ultra port could be detected." >&2
    printf '%s\n' "$PORTS_OUTPUT" >&2
    exit 2
  fi

  if ! printf '%s\n' "$PORTS_OUTPUT" | grep -qw "$PORT"; then
    echo "ERROR: port $PORT was not listed by 'app-ports free'." >&2
    printf '%s\n' "$PORTS_OUTPUT" >&2
    exit 3
  fi
elif [[ -z "$PORT" ]]; then
  echo "ERROR: app-ports is unavailable and no explicit port was supplied." >&2
  echo "Usage: bash deploy/ultra/install.sh [assigned-5-digit-port]" >&2
  exit 2
else
  echo "WARNING: app-ports command not found; cannot verify Ultra port allocation." >&2
fi

if ! [[ "$PORT" =~ ^[0-9]{5}$ ]]; then
  echo "ERROR: Ultra custom-app port must be a 5-digit assigned port; got '$PORT'." >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
STATE_DIR="$HOME/.local/share/$APP_NAME"
VENV_DIR="$STATE_DIR/venv"
ENV_FILE="$STATE_DIR/mykoknoks.env"
DEPLOY_INFO="$STATE_DIR/deployment.env"
LITE_STORE="$STATE_DIR/features.sqlite"
INIT_STORE="$REPO_ROOT/scripts/init_lite_feature_store.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/$APP_NAME.service"
NGINX_DIR="$HOME/.apps/nginx/proxy.d"
NGINX_FILE="$NGINX_DIR/$APP_NAME.conf"

if [[ ! -f "$BACKEND_DIR/pyproject.toml" ]]; then
  echo "ERROR: backend/pyproject.toml not found. Run this installer from a MykoKnoks checkout." >&2
  exit 4
fi
if [[ ! -f "$INIT_STORE" ]]; then
  echo "ERROR: scripts/init_lite_feature_store.py not found." >&2
  exit 4
fi

PYTHON="$(command -v python3 || true)"
if [[ -z "$PYTHON" ]]; then
  echo "ERROR: python3 is not available in PATH." >&2
  exit 5
fi

mkdir -p "$STATE_DIR" "$SERVICE_DIR" "$NGINX_DIR"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  "$PYTHON" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -e "$BACKEND_DIR"
"$VENV_DIR/bin/python" "$INIT_STORE" "$LITE_STORE"

cat > "$ENV_FILE" <<EOF
APP_ENV=production
APP_NAME=MykoKnoks
APP_VERSION=0.2.4
API_PREFIX=/api/v1
ROOT_PATH=${BASE_PATH}
CORS_ORIGINS=https://appassets.androidplatform.net,https://${PUBLIC_HOST}
DATABASE_URL=sqlite:///${LITE_STORE}
MET_USER_AGENT=MykoKnoks/0.2.4 https://github.com/knoksen/MykoKnoks
MET_TIMEOUT_SECONDS=10
UPSTREAM_TIMEOUT_SECONDS=20
DEFAULT_H3_RESOLUTION=9
LIVE_CELL_LIMIT=36
LIVE_FEATURE_CONCURRENCY=8
EOF
chmod 600 "$ENV_FILE"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=MykoKnoks FastAPI ecological intelligence API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --app-dir $BACKEND_DIR --host 127.0.0.1 --port $PORT --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5
TimeoutStopSec=20

[Install]
WantedBy=default.target
EOF

# A trailing slash on proxy_pass intentionally strips BASE_PATH before requests
# reach FastAPI. ROOT_PATH tells FastAPI the public prefix for generated URLs.
cat > "$NGINX_FILE" <<EOF
location ${BASE_PATH}/ {
    proxy_pass              http://127.0.0.1:${PORT}/;
    proxy_http_version      1.1;
    proxy_set_header        Host                    \$host;
    proxy_set_header        X-Real-IP               \$remote_addr;
    proxy_set_header        X-Forwarded-For         \$proxy_add_x_forwarded_for;
    proxy_set_header        X-Forwarded-Proto       \$scheme;
    proxy_set_header        X-Forwarded-Host        \$http_host;
    proxy_read_timeout      90s;
}
EOF

cat > "$DEPLOY_INFO" <<EOF
MYKOKNOKS_PORT=$PORT
MYKOKNOKS_API_BASE=https://${PUBLIC_HOST}${BASE_PATH}
MYKOKNOKS_HEALTH=https://${PUBLIC_HOST}${BASE_PATH}/health
MYKOKNOKS_FEATURE_STORE=${LITE_STORE}
EOF
chmod 600 "$DEPLOY_INFO"

systemctl --user daemon-reload
systemctl --user enable --now "$APP_NAME.service"
systemctl --user is-active --quiet "$APP_NAME.service"

if command -v app-nginx >/dev/null 2>&1; then
  app-nginx restart
else
  echo "WARNING: app-nginx command not found. Restart the Ultra webserver from UCP." >&2
fi

sleep 2

echo "Checking local API..."
curl --fail --silent --show-error "http://127.0.0.1:${PORT}/health"
echo

PUBLIC_URL="https://${PUBLIC_HOST}${BASE_PATH}"
echo "Checking public HTTPS proxy..."
if curl --fail --silent --show-error --max-time 15 "${PUBLIC_URL}/health"; then
  echo
  PUBLIC_STATUS="reachable"
else
  PUBLIC_STATUS="not-yet-reachable"
  echo "WARNING: local API works, but the public proxy health check did not succeed yet." >&2
  echo "If Nginx was just restarted, retry: curl -fsS ${PUBLIC_URL}/health" >&2
fi

echo ""
echo "MykoKnoks Ultra deployment installed."
echo "Port:    $PORT"
echo "Local:   http://127.0.0.1:${PORT}/health"
echo "Public:  ${PUBLIC_URL}"
echo "Store:   ${LITE_STORE}"
echo "Status:  ${PUBLIC_STATUS}"
echo "Config:  $ENV_FILE"
echo "Deploy:  $DEPLOY_INFO"
echo "Logs:    journalctl --user -u ${APP_NAME}.service -n 100 --no-pager"
