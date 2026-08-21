#!/usr/bin/env bash
set -u

APP_NAME="mykoknoks"
STATE_DIR="$HOME/.local/share/$APP_NAME"
VENV_PY="$STATE_DIR/venv/bin/python"
DEPLOY_INFO="$STATE_DIR/deployment.env"
PUBLIC_DEFAULT="https://knoksen.nova.usbx.me/mykoknoks-api"

PORT=""
PUBLIC_URL="$PUBLIC_DEFAULT"
STORE="$STATE_DIR/features.sqlite"
if [[ -f "$DEPLOY_INFO" ]]; then
  # shellcheck disable=SC1090
  source "$DEPLOY_INFO"
  PORT="${MYKOKNOKS_PORT:-}"
  PUBLIC_URL="${MYKOKNOKS_API_BASE:-$PUBLIC_DEFAULT}"
  STORE="${MYKOKNOKS_FEATURE_STORE:-$STORE}"
fi

echo "MykoKnoks Ultra status"
echo "======================="
echo "Service:"
systemctl --user --no-pager --full status "$APP_NAME.service" || true

echo ""
echo "Deployment metadata:"
if [[ -f "$DEPLOY_INFO" ]]; then
  cat "$DEPLOY_INFO"
else
  echo "not installed: $DEPLOY_INFO"
fi

echo ""
if [[ -n "$PORT" ]]; then
  echo "Local health:"
  if curl -fsS --max-time 10 "http://127.0.0.1:${PORT}/health"; then
    echo
  else
    echo "FAILED"
  fi
else
  echo "Local health: unknown port"
fi

echo ""
echo "Public HTTPS health:"
if curl -fsS --max-time 15 "${PUBLIC_URL}/health"; then
  echo
else
  echo "FAILED: ${PUBLIC_URL}/health"
fi

echo ""
echo "H3 feature store:"
if [[ -f "$STORE" && -x "$VENV_PY" ]]; then
  "$VENV_PY" - "$STORE" <<'PY'
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1])
with sqlite3.connect(path) as conn:
    features = conn.execute("SELECT COUNT(*) FROM env_features").fetchone()[0]
    evidence = conn.execute("SELECT COUNT(*) FROM env_feature_evidence").fetchone()[0]
print(f"path={path}")
print(f"size_bytes={path.stat().st_size}")
print(f"feature_rows={features}")
print(f"evidence_rows={evidence}")
PY
else
  echo "not initialized: $STORE"
fi

echo ""
echo "Recent logs:"
journalctl --user -u "$APP_NAME.service" -n 30 --no-pager || true
