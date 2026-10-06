#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if [[ ! -d .venv ]]; then
  echo "Crea .venv e instala requirements antes de correr." >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3009}"
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
