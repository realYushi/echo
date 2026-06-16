#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NETWORK_NAME="echo"
POSTGRES_NAME="echo-postgres"
QDRANT_NAME="echo-qdrant"
BACKEND_NAME="echo-backend"
FRONTEND_NAME="echo-frontend"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

stop_if_exists() {
  local name="$1"

  if container inspect "${name}" >/dev/null 2>&1; then
    container stop "${name}" >/dev/null 2>&1 || true
    container rm "${name}" >/dev/null 2>&1 || true
  fi
}

env_value() {
  local key="$1"
  local default_value="${2:-}"
  local value=""

  if [[ -v "${key}" ]]; then
    printf '%s' "${!key}"
    return 0
  fi

  for env_file in "${ROOT_DIR}/.env" "${ROOT_DIR}/backend/.env"; do
    if [[ -f "${env_file}" ]]; then
      value="$(grep -E "^${key}=" "${env_file}" | tail -n 1 || true)"
      if [[ -n "${value}" ]]; then
        value="${value#*=}"
        value="${value%$'\r'}"
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        printf '%s' "${value}"
        return 0
      fi
    fi
  done

  printf '%s' "${default_value}"
}

ensure_network() {
  if ! container network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    container network create "${NETWORK_NAME}"
  fi
}

container_ip() {
  local name="$1"

  container inspect "${name}" | python3 -c 'import json, sys; network = json.load(sys.stdin)[0]["status"]["networks"][0]; print((network.get("address") or network.get("ipv4Address")).split("/")[0])'
}

wait_for_host_http() {
  local url="$1"
  local attempts=60

  for _ in $(seq 1 "${attempts}"); do
    if python3 -c "import urllib.request; urllib.request.urlopen('${url}', timeout=2).read()" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for ${url}." >&2
  exit 1
}

wait_for_backend() {
  local attempts=300

  for _ in $(seq 1 "${attempts}"); do
    if container logs "${BACKEND_NAME}" 2>&1 | grep -q "Application startup complete"; then
      return 0
    fi

    if ! container inspect "${BACKEND_NAME}" >/dev/null 2>&1; then
      echo "Backend container exited before startup completed." >&2
      exit 1
    fi

    sleep 1
  done

  echo "Timed out waiting for backend startup." >&2
  container logs "${BACKEND_NAME}" 2>&1 | tail -120 >&2 || true
  exit 1
}

require_command container
require_command python3

container system start
ensure_network

mkdir -p \
  "${ROOT_DIR}/.containers/postgres_data" \
  "${ROOT_DIR}/.containers/qdrant_data" \
  "${ROOT_DIR}/.containers/huggingface"

stop_if_exists "${FRONTEND_NAME}"
stop_if_exists "${BACKEND_NAME}"
stop_if_exists "${QDRANT_NAME}"
stop_if_exists "${POSTGRES_NAME}"

echo "Starting Postgres and Qdrant..."
container run \
  --name "${POSTGRES_NAME}" \
  --detach \
  --network "${NETWORK_NAME}" \
  --publish 5432:5432 \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_PASSWORD=postgres \
  --env POSTGRES_DB=echo \
  --env PGDATA=/var/lib/postgresql/data/pgdata \
  --volume "${ROOT_DIR}/.containers/postgres_data:/var/lib/postgresql/data" \
  postgres:16-alpine >/dev/null

container run \
  --name "${QDRANT_NAME}" \
  --detach \
  --network "${NETWORK_NAME}" \
  --publish 6333:6333 \
  --publish 6334:6334 \
  --volume "${ROOT_DIR}/.containers/qdrant_data:/qdrant/storage" \
  qdrant/qdrant:latest >/dev/null

wait_for_host_http "http://127.0.0.1:6333/"

POSTGRES_IP="$(container_ip "${POSTGRES_NAME}")"
QDRANT_IP="$(container_ip "${QDRANT_NAME}")"
ANTHROPIC_API_KEY_VALUE="$(env_value ANTHROPIC_API_KEY)"
ANTHROPIC_MODEL_VALUE="$(env_value ANTHROPIC_MODEL claude-3-5-sonnet-latest)"
ANTHROPIC_POST_PROCESS_MODEL_VALUE="$(env_value ANTHROPIC_POST_PROCESS_MODEL claude-haiku-4-5-20251001)"
GEMINI_API_KEY_VALUE="$(env_value GEMINI_API_KEY)"
GEMINI_LIVE_MODEL_VALUE="$(env_value GEMINI_LIVE_MODEL gemini-3.1-flash-live-preview)"
DEBUG_VALUE="$(env_value DEBUG false)"

build_backend() {
  echo "Building backend image..."
  container build --tag echo-backend:latest "${ROOT_DIR}/backend"
}

build_frontend() {
  local backend_url="$1"

  echo "Building frontend image..."
  container build \
    --tag echo-frontend:latest \
    --build-arg "NEXT_PUBLIC_API_URL=${backend_url}" \
    "${ROOT_DIR}/frontend"
}

build_backend

echo "Starting backend..."
container run \
  --name "${BACKEND_NAME}" \
  --detach \
  --memory 8G \
  --network "${NETWORK_NAME}" \
  --publish 8000:8000 \
  --volume "${ROOT_DIR}/.containers/huggingface:/cache/huggingface" \
  --env "DATABASE_URL=postgresql+asyncpg://postgres:postgres@${POSTGRES_IP}:5432/echo" \
  --env "QDRANT_URL=http://${QDRANT_IP}:6333" \
  --env "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_VALUE}" \
  --env "ANTHROPIC_MODEL=${ANTHROPIC_MODEL_VALUE}" \
  --env "ANTHROPIC_POST_PROCESS_MODEL=${ANTHROPIC_POST_PROCESS_MODEL_VALUE}" \
  --env "GEMINI_API_KEY=${GEMINI_API_KEY_VALUE}" \
  --env "GEMINI_LIVE_MODEL=${GEMINI_LIVE_MODEL_VALUE}" \
  --env "DEBUG=${DEBUG_VALUE}" \
  --env HF_HOME=/cache/huggingface \
  echo-backend:latest >/dev/null

wait_for_backend

BACKEND_IP="$(container_ip "${BACKEND_NAME}")"
build_frontend "http://${BACKEND_IP}:8000"

echo "Starting frontend..."
container run \
  --name "${FRONTEND_NAME}" \
  --detach \
  --network "${NETWORK_NAME}" \
  --publish 3000:3000 \
  --env "NEXT_PUBLIC_API_URL=http://${BACKEND_IP}:8000" \
  echo-frontend:latest >/dev/null

sleep 2

echo
echo "Containerized app stack is running."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo
echo "Stop it with: make container-down"
