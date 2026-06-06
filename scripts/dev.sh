#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

cleanup() {
  local exit_code=$?

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi

  wait "${BACKEND_PID}" 2>/dev/null || true
  wait "${FRONTEND_PID}" 2>/dev/null || true

  exit "${exit_code}"
}

trap cleanup INT TERM EXIT

require_command docker
require_command uv
require_command npm

echo "Starting Postgres and Qdrant with docker compose..."
(cd "${ROOT_DIR}" && docker-compose up -d)

echo "Starting backend on http://127.0.0.1:8000 ..."
(
  cd "${ROOT_DIR}/backend"
  uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:3000 ..."
(
  cd "${ROOT_DIR}/frontend"
  npm run dev
) &
FRONTEND_PID=$!

echo
echo "App stack is launching."
echo "Frontend: http://127.0.0.1:3000"
echo "Backend:  http://127.0.0.1:8000"
echo "API docs: http://127.0.0.1:8000/docs"
echo
echo "Press Ctrl+C to stop the frontend and backend."
echo "Docker services stay up; run 'make down' if you want to stop Postgres and Qdrant too."

wait "${BACKEND_PID}" "${FRONTEND_PID}"
