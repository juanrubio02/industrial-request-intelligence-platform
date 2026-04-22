#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./dev-common.sh
source "$SCRIPT_DIR/dev-common.sh"

#######################################
# Requirements
#######################################

require_command docker
require_command npm
require_command curl

# Detect docker compose command
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

#######################################
# Cross-platform port check (frontend only)
#######################################

is_port_in_use() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP -sTCP:LISTEN -P | grep -q ":$port "
  else
    netstat -an 2>/dev/null | grep -q "\.$port "
  fi
}

find_free_port() {
  local port=$1
  while is_port_in_use "$port"; do
    port=$((port + 1))
  done
  echo "$port"
}

#######################################
# Args
#######################################

REBUILD_IMAGES=false
if [[ "${1:-}" == "--rebuild" ]]; then
  REBUILD_IMAGES=true
fi

#######################################
# Install frontend deps
#######################################

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (
    cd "$FRONTEND_DIR"
    npm install
  )
fi

#######################################
# Frontend dynamic port
#######################################

FRONTEND_PORT=$(find_free_port "$FRONTEND_PORT")

FRONTEND_PUBLIC_URL="http://localhost:$FRONTEND_PORT"
FRONTEND_URL="$FRONTEND_PUBLIC_URL"

#######################################
# Cleanup stale frontend process
#######################################

clear_stale_frontend_pid

#######################################
# Start backend (Docker)
#######################################

echo "Starting backend, PostgreSQL and Redis..."

if $REBUILD_IMAGES; then
  $COMPOSE_CMD up -d --build postgres redis backend
else
  $COMPOSE_CMD up -d postgres redis backend
fi

#######################################
# Detect real backend port (Docker dynamic)
#######################################

echo "Detecting backend port assigned by Docker..."

CONTAINER_NAME=$($COMPOSE_CMD ps -q backend)

BACKEND_PORT_REAL=$(docker port "$CONTAINER_NAME" 8000 | head -n1 | awk -F: '{print $2}')
BACKEND_PUBLIC_URL="http://localhost:$BACKEND_PORT_REAL"
BACKEND_URL="$BACKEND_PUBLIC_URL"

echo "Using ports:"
echo "  Backend:  $BACKEND_PORT_REAL"
echo "  Frontend: $FRONTEND_PORT"

#######################################
# Wait backend
#######################################

wait_for_http "$BACKEND_URL/health" "Backend API" 90

#######################################
# Write frontend env (NOW correct)
#######################################

write_frontend_env

#######################################
# Seed data
#######################################

echo "Seeding demo workspace..."
$COMPOSE_CMD exec -T backend python scripts/seed_demo.py >/dev/null

#######################################
# Start frontend
#######################################

if frontend_pid_running && http_ready "$FRONTEND_URL/login"; then
  echo "Frontend already running on $FRONTEND_PUBLIC_URL"
else
  echo "Starting frontend on $FRONTEND_PUBLIC_URL..."

  : > "$FRONTEND_LOG_FILE"

  (
    cd "$FRONTEND_DIR"
    nohup npm run dev -- -p "$FRONTEND_PORT" >>"$FRONTEND_LOG_FILE" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
  )

  wait_for_http "$FRONTEND_URL/login" "Frontend app" 90

  LISTENER_PID="$(frontend_listener_pid)"
  if [[ -z "$LISTENER_PID" ]]; then
    echo "Frontend started but no listener PID detected." >&2
    exit 1
  fi

  echo "$LISTENER_PID" > "$FRONTEND_PID_FILE"
fi

#######################################
# Final output
#######################################

cat <<EOF

🚀 Development environment ready

Frontend:
  $FRONTEND_PUBLIC_URL/login

Backend:
  $BACKEND_PUBLIC_URL/health

Commands:
  ./scripts/dev-check.sh
  ./scripts/dev-logs.sh
  ./scripts/dev-down.sh

Rebuild:
  ./scripts/dev-up.sh --rebuild

Demo credentials:
  email: $DEMO_USER_EMAIL
  password: $DEMO_USER_PASSWORD

EOF