#!/usr/bin/env bash
# One command. Serves data/processed/close.json (Dataset 01) by default.
#   PACK=02 ./run.sh            → Dataset 02 close (data/processed/close-dataset02.json)
#   CLOSE_FILE=path ./run.sh    → any canonical close (e.g. a pilot copy)
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8378}"
if [[ -n "${PACK:-}" && -z "${CLOSE_FILE:-}" ]]; then
  case "$PACK" in
    01) CLOSE_FILE="data/processed/close.json" ;;
    02) CLOSE_FILE="data/processed/close-dataset02.json" ;;
    *) echo "PACK must be 01 or 02" >&2; exit 2 ;;
  esac
fi
if [[ -n "${CLOSE_FILE:-}" ]]; then
  exec python3 -m app.server --port "$PORT" --close "$CLOSE_FILE"
fi
exec python3 -m app.server --port "$PORT"
