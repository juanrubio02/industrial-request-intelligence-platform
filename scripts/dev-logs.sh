#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./dev-common.sh
source "$SCRIPT_DIR/dev-common.sh"

if [[ -f "$FRONTEND_LOG_FILE" ]]; then
  echo "Streaming frontend log from $FRONTEND_LOG_FILE"
  tail -n 80 -f "$FRONTEND_LOG_FILE" &
  TAIL_PID=$!
  trap 'kill "$TAIL_PID" >/dev/null 2>&1 || true' EXIT
else
  echo "Frontend log file not found yet: $FRONTEND_LOG_FILE"
fi

compose logs -f backend postgres redis
