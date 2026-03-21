#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env
if [ -f ".env" ]; then
  export $(grep -v '^\s*#' .env | xargs)
fi

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Apply defaults
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "Starting FastAPI on http://${HOST}:${PORT}"
uvicorn main:app --host "$HOST" --port "$PORT" --reload
