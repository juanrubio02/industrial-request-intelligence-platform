#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./dev-common.sh
source "$SCRIPT_DIR/dev-common.sh"

FRONTEND_PID=""
if frontend_pid_running; then
  FRONTEND_PID="$(cat "$FRONTEND_PID_FILE")"
else
  FRONTEND_PID="$(frontend_listener_pid)"
fi

if [[ -n "$FRONTEND_PID" ]]; then
  echo "Stopping frontend dev server..."
  kill "$FRONTEND_PID"
  rm -f "$FRONTEND_PID_FILE"
else
  clear_stale_frontend_pid
fi

echo "Stopping backend, PostgreSQL and Redis..."
compose down --remove-orphans

echo "Development environment stopped."
