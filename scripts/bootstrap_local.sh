#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT="${BACKEND_PORT:-28000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

pick_free_port() {
  "$BACKEND_DIR/.venv/bin/python" - "$@" <<'PY'
from __future__ import annotations

import socket
import sys

for raw_port in sys.argv[1:]:
    port = int(raw_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        raise SystemExit(0)

raise SystemExit(1)
PY
}

BACKEND_PORT="$(pick_free_port "$BACKEND_PORT" 28000 29000 30080 38000 48000)"

echo "Preparing frontend .env.local..."
printf 'NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:%s\n' "$BACKEND_PORT" > "$FRONTEND_DIR/.env.local"

echo "Starting backend, PostgreSQL and Redis in Docker..."
BACKEND_PORT="$BACKEND_PORT" docker compose -f "$ROOT_DIR/docker-compose.yml" up -d --build backend postgres redis

echo "Waiting for backend API to become available..."
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null 2>&1; then
  echo "Backend did not become ready on http://127.0.0.1:${BACKEND_PORT}/health"
  echo "Inspect logs with:"
  echo "  docker compose logs backend --tail=200"
  exit 1
fi

echo "Seeding demo workspace inside backend container..."
docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T backend python scripts/seed_demo.py

cat <<EOF

Bootstrap complete.

Frontend:
  cd $FRONTEND_DIR
  npm run dev -- --port $FRONTEND_PORT

Then open:
  http://localhost:$FRONTEND_PORT/login

Backend API:
  http://127.0.0.1:$BACKEND_PORT

Demo credentials:
  email: admin@acme.com
  password: Admin1234

EOF
