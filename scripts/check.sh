#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/ruff check apps/api
.venv/bin/ruff format --check apps/api
.venv/bin/mypy --config-file apps/api/pyproject.toml apps/api/akus
AKUS_DATABASE_URL="${AKUS_TEST_DATABASE_URL:-postgresql+psycopg://akus_demo:akus_demo@127.0.0.1:55432/akus_test}" .venv/bin/alembic -c apps/api/alembic.ini upgrade head
AKUS_DATABASE_URL="${AKUS_TEST_DATABASE_URL:-postgresql+psycopg://akus_demo:akus_demo@127.0.0.1:55432/akus_test}" .venv/bin/alembic -c apps/api/alembic.ini check
.venv/bin/pytest apps/api/tests -q
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web test
npm --prefix apps/web run build
