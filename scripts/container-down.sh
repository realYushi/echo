#!/usr/bin/env bash

set -euo pipefail

for name in echo-frontend echo-backend echo-qdrant echo-postgres; do
  if container inspect "${name}" >/dev/null 2>&1; then
    container stop "${name}" >/dev/null 2>&1 || true
    container rm "${name}" >/dev/null 2>&1 || true
  fi
done

echo "Containerized app stack stopped."
