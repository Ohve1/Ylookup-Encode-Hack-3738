#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8378}"
exec python3 -m app.server --port "$PORT"
