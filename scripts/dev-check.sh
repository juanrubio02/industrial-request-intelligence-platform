#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./dev-common.sh
source "$SCRIPT_DIR/dev-common.sh"

require_command curl

DEEP_CHECK=false
if [[ "${1:-}" == "--deep" ]]; then
  DEEP_CHECK=true
fi

wait_for_http "$BACKEND_URL/health" "Backend API" 5
wait_for_http "$FRONTEND_URL/login" "Frontend app" 5

BACKEND_HEALTH="$(curl -fsS "$BACKEND_URL/health")"
echo "Backend health: $BACKEND_HEALTH"
echo "Frontend login page: reachable on $FRONTEND_PUBLIC_URL/login"

BACKEND_URL="$BACKEND_URL" \
DEMO_USER_EMAIL="$DEMO_USER_EMAIL" \
DEMO_USER_PASSWORD="$DEMO_USER_PASSWORD" \
DEEP_CHECK="$DEEP_CHECK" \
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

base_url = os.environ["BACKEND_URL"]
email = os.environ["DEMO_USER_EMAIL"]
password = os.environ["DEMO_USER_PASSWORD"]
deep_check = os.environ["DEEP_CHECK"].lower() == "true"


def request(
    path: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> dict | list:
    body = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {path} failed with HTTP {exc.code}: {details}") from exc


login_payload = request(
    "/auth/login",
    method="POST",
    payload={"email": email, "password": password},
)
token = login_payload["access_token"]
auth_headers = {"Authorization": f"Bearer {token}"}

memberships = request("/auth/memberships", headers=auth_headers)
if not memberships:
    raise SystemExit("No active memberships were returned for the demo user.")

membership_id = memberships[0]["id"]
scenarios = request(
    "/demo/intake/scenarios",
    headers={**auth_headers, "X-Membership-Id": membership_id},
)
if not scenarios:
    raise SystemExit("No demo intake scenarios were returned.")

print(f"Demo login: ok ({email})")
print(f"Memberships: {len(memberships)}")
print(f"Demo intake scenarios: {len(scenarios)}")

if deep_check:
    scenario_key = scenarios[0]["key"]
    run_result = request(
        f"/demo/intake/scenarios/{scenario_key}/run",
        method="POST",
        headers={**auth_headers, "X-Membership-Id": membership_id},
    )
    print(f"Deep demo intake run: ok ({scenario_key} -> request {run_result['request_id']})")
PY
