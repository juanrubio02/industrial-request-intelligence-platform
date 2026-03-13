#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./dev-common.sh
source "$SCRIPT_DIR/dev-common.sh"

require_command docker
require_command npm
require_command curl
require_command ss

REBUILD_IMAGES=false
if [[ "${1:-}" == "--rebuild" ]]; then
  REBUILD_IMAGES=true
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run 'cd frontend && npm install' once before dev-up." >&2
  exit 1
fi

clear_stale_frontend_pid
ensure_port_available_or_expected "$BACKEND_PORT" "$BACKEND_URL/health" "backend"
ensure_port_available_or_expected "$FRONTEND_PORT" "$FRONTEND_URL/login" "frontend"

write_frontend_env

echo "Starting backend, PostgreSQL and Redis on fixed development ports..."
if $REBUILD_IMAGES; then
  compose up -d --build postgres redis backend
else
  compose up -d postgres redis backend
fi
wait_for_http "$BACKEND_URL/health" "Backend API" 90

echo "Seeding demo workspace..."
compose exec -T backend python scripts/seed_demo.py >/dev/null

if frontend_pid_running && http_ready "$FRONTEND_URL/login"; then
  echo "Frontend dev server is already running on $FRONTEND_PUBLIC_URL."
else
  echo "Starting frontend dev server on $FRONTEND_PUBLIC_URL..."
  : > "$FRONTEND_LOG_FILE"
  (
    cd "$FRONTEND_DIR"
    nohup npm run dev >>"$FRONTEND_LOG_FILE" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
  )
  wait_for_http "$FRONTEND_URL/login" "Frontend app" 90
  LISTENER_PID="$(frontend_listener_pid)"
  if [[ -z "$LISTENER_PID" ]]; then
    echo "Frontend started but no listener PID was detected on port $FRONTEND_PORT." >&2
    exit 1
  fi
  echo "$LISTENER_PID" > "$FRONTEND_PID_FILE"
fi

cat <<EOF

Development environment is ready.

Frontend:
  $FRONTEND_PUBLIC_URL/login

Backend:
  $BACKEND_PUBLIC_URL/health

Official checks:
  ./scripts/dev-check.sh
  ./scripts/dev-logs.sh

Rebuild backend image when dependencies change:
  ./scripts/dev-up.sh --rebuild

Official stop:
  ./scripts/dev-down.sh

Demo credentials:
  email: $DEMO_USER_EMAIL
  password: $DEMO_USER_PASSWORD
EOF
