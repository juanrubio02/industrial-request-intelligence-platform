#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "bootstrap_local.sh is deprecated. Running the official development entrypoint instead."
exec "$SCRIPT_DIR/dev-up.sh"
