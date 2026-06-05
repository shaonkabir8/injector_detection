#!/usr/bin/env bash
set -euo pipefail

SERVICE_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

# Determine package manager for Node-based services.
find_package_manager() {
  if command -v pnpm >/dev/null 2>&1; then
    echo pnpm
  elif command -v npm >/dev/null 2>&1; then
    echo npm
  elif command -v yarn >/dev/null 2>&1; then
    echo yarn
  else
    echo "";
  fi
}

PM="$(find_package_manager)"
if [[ -z "$PM" ]]; then
  echo "[startup] ERROR: No package manager found. Install pnpm, npm, or yarn."
  exit 1
fi

cd "$SERVICE_DIR"

start_ui() {
  local port="${UI_PORT:-5174}"
  echo "[startup] Starting UI on port ${port}..."
  PORT="${port}" "$PM" --prefix ui run dev
}

start_frontend() {
  local port="${FRONTEND_PORT:-5173}"
  echo "[startup] Starting frontend dashboard on port ${port}..."
  PORT="${port}" "$PM" --prefix frontend run dev
}

start_server() {
  local port="${SERVER_PORT:-4000}"
  echo "[startup] Starting API server on port ${port}..."
  PORT="${port}" "$PM" --prefix server run dev
}

start_detector() {
  local port="${DETECTOR_PORT:-5000}"
  echo "[startup] Python: $($PYTHON --version 2>&1)"
  echo "[startup] Starting Detector on port ${port}..."
  export BASE_PATH="${BASE_PATH:-/detect}"
  export PORT="${port}"
  exec "$PYTHON" -m uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --workers 1
}

start_all() {
  local ui_port="${UI_PORT:-5174}"
  local frontend_port="${FRONTEND_PORT:-5173}"
  local server_port="${SERVER_PORT:-4000}"
  local detector_port="${DETECTOR_PORT:-5000}"

  echo "[startup] Starting all services..."
  echo "[startup] UI -> http://localhost:${ui_port}"
  echo "[startup] Frontend -> http://localhost:${frontend_port}"
  echo "[startup] Server -> http://localhost:${server_port}"
  echo "[startup] Detector -> http://localhost:${detector_port}"

  PORT="${ui_port}" "$PM" --prefix ui run dev &
  ui_pid=$!

  PORT="${frontend_port}" "$PM" --prefix frontend run dev &
  frontend_pid=$!

  PORT="${server_port}" "$PM" --prefix server run dev &
  server_pid=$!

  BASE_PATH="${BASE_PATH:-/detect}" PORT="${detector_port}" "$PYTHON" -m uvicorn main:app \
    --host 0.0.0.0 \
    --port "${detector_port}" \
    --log-level info \
    --workers 1 &
  detector_pid=$!

  trap 'echo "[startup] Shutting down..."; kill "$ui_pid" "$frontend_pid" "$server_pid" "$detector_pid" 2>/dev/null || true; wait' INT TERM EXIT
  wait
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [ui|frontend|server|detector|all]

Commands:
  ui         Start the Next.js admin UI (ui/)
  frontend   Start the Vite detector dashboard (frontend/)
  server     Start the Node API server (server/)
  detector   Start the Python detector service (root)
  all        Start UI, frontend, server, and detector together

Environment variables:
  UI_PORT         default 5174
  FRONTEND_PORT   default 5173
  SERVER_PORT     default 4000
  DETECTOR_PORT   default 5000
  BASE_PATH       default /detect for detector
EOF
}

case "${1:-detector}" in
  ui)
    start_ui
    ;;
  frontend)
    start_frontend
    ;;
  server)
    start_server
    ;;
  detector)
    start_detector
    ;;
  all)
    start_all
    ;;
  -*|help|--help)
    usage
    ;;
  "")
    start_detector
    ;;
  *)
    echo "[startup] ERROR: Unknown service '$1'"
    usage
    exit 1
    ;;
esac
