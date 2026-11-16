#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export AKUS_ENV=local AKUS_DEMO_ENABLED=true
export AKUS_PUBLIC_ORIGIN="${AKUS_PUBLIC_ORIGIN:-http://127.0.0.1:5173}"
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python -m akus.seed
.venv/bin/uvicorn akus.main:create_app --factory --host 127.0.0.1 --port 8000 & api_pid=$!
.venv/bin/python -m akus.worker & worker_pid=$!
(cd apps/web && exec node node_modules/vite/bin/vite.js --host 127.0.0.1) & web_pid=$!
trap 'kill "$api_pid" "$worker_pid" "$web_pid" 2>/dev/null || true' EXIT INT TERM
wait -n "$api_pid" "$worker_pid" "$web_pid"
