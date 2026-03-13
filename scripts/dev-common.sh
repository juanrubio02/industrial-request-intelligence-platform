#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
FRONTEND_DIR="$ROOT_DIR/frontend"
FRONTEND_ENV_FILE="$FRONTEND_DIR/.env.local"
RUNTIME_DIR="$ROOT_DIR/.dev-runtime"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
FRONTEND_LOG_FILE="$RUNTIME_DIR/frontend.log"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
BACKEND_PUBLIC_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_HOST="127.0.0.1"
FRONTEND_PORT="3000"
FRONTEND_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
FRONTEND_PUBLIC_URL="http://localhost:${FRONTEND_PORT}"
DEMO_USER_EMAIL="${DEMO_USER_EMAIL:-admin@acme.com}"
DEMO_USER_PASSWORD="${DEMO_USER_PASSWORD:-Admin1234}"

mkdir -p "$RUNTIME_DIR"

resolve_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi

  echo "Python is required but was not found in PATH." >&2
  exit 1
}

PYTHON_BIN="${PYTHON_BIN:-$(resolve_python)}"

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
}

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

port_is_open() {
  "$PYTHON_BIN" - "$1" <<'PY'
from __future__ import annotations

import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.3)
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", port)) == 0 else 1)
PY
}

http_ready() {
  local url="$1"
  curl -fsS "$url" >/dev/null 2>&1
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local attempts="${3:-60}"

  for _ in $(seq 1 "$attempts"); do
    if http_ready "$url"; then
      return 0
    fi
    sleep 1
  done

  echo "$label did not become ready at $url" >&2
  return 1
}

write_frontend_env() {
  printf 'NEXT_PUBLIC_API_BASE_URL=%s\n' "$BACKEND_PUBLIC_URL" > "$FRONTEND_ENV_FILE"
}

frontend_pid_running() {
  if [[ ! -f "$FRONTEND_PID_FILE" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$FRONTEND_PID_FILE")"
  [[ -n "$pid" ]] && ps -p "$pid" >/dev/null 2>&1
}

clear_stale_frontend_pid() {
  if [[ -f "$FRONTEND_PID_FILE" ]] && ! frontend_pid_running; then
    rm -f "$FRONTEND_PID_FILE"
  fi
}

frontend_listener_pid() {
  ss -ltnp "( sport = :${FRONTEND_PORT} )" 2>/dev/null \
    | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
    | head -n 1
}

ensure_port_available_or_expected() {
  local port="$1"
  local expected_url="$2"
  local label="$3"

  if ! port_is_open "$port"; then
    return 0
  fi

  if http_ready "$expected_url"; then
    return 0
  fi

  echo "Port $port is already in use and does not look like the expected $label service." >&2
  exit 1
}
