#!/usr/bin/env bash
set -e

SERVICE_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

echo "[startup] Python: $($PYTHON --version 2>&1)"
echo "[startup] Starting Vehicle Detector on port ${PORT:-5000}..."

export BASE_PATH="${BASE_PATH:-/detect}"
export PORT="${PORT:-5000}"

cd "$SERVICE_DIR"
exec $PYTHON -m uvicorn main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --log-level info \
  --workers 1
