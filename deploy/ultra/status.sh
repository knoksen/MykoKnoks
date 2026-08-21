#!/usr/bin/env bash
set -u

APP_NAME="mykoknoks"
STATE_DIR="$HOME/.local/share/$APP_NAME"
DEPLOY_INFO="$STATE_DIR/deployment.env"
PUBLIC_DEFAULT="https://knoksen.nova.usbx.me/mykoknoks-api"

PORT=""
PUBLIC_URL="$PUBLIC_DEFAULT"
if [[ -f "$DEPLOY_INFO" ]]; then
  # shellcheck disable=SC1090
  source "$DEPLOY_INFO"
  PORT="${MYKOKNOKS_PORT:-}"
  PUBLIC_URL="${MYKOKNOKS_API_BASE:-$PUBLIC_DEFAULT}"
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
echo "Recent logs:"
journalctl --user -u "$APP_NAME.service" -n 30 --no-pager || true
