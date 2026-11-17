#!/usr/bin/env bash
# Linux / macOS / Android (Termux) launcher.
#   ./scripts/start.sh          run the monolith  (http://localhost:8000)
#   ./scripts/start.sh micro    run the microservices (gateway + query + data + history + chart)
# Optional: QUERYX_HOST=0.0.0.0 to allow other devices on your network, QUERYX_PORT=8000
set -e
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [ "$1" = "micro" ]; then
  exec python scripts/run_microservices.py
fi
exec python -m uvicorn app.main:app --host "${QUERYX_HOST:-127.0.0.1}" --port "${QUERYX_PORT:-8000}"
