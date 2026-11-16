#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
AKUS_CHECK_DB="${AKUS_TEST_DATABASE_NAME:-akus_completion_test}"
if [[ ! "$AKUS_CHECK_DB" =~ ^[a-z][a-z0-9_]*_test$ ]]; then
  echo 'An isolated database name ending _test is required.' >&2
  exit 1
fi
exists=$(docker compose exec -T db psql -U akus_demo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$AKUS_CHECK_DB'")
if [[ "$exists" != 1 ]]; then
  docker compose exec -T db createdb -U akus_demo "$AKUS_CHECK_DB"
fi
docker compose run --rm --no-deps -v "$PWD/apps/api:/app/apps/api:ro" \
  -e AKUS_ENV=test -e AKUS_DEMO_ENABLED=true \
  -e "AKUS_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/$AKUS_CHECK_DB" \
  -e "AKUS_TEST_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/$AKUS_CHECK_DB" \
  -e AKUS_PUBLIC_ORIGIN=http://127.0.0.1:5173 \
  -e AKUS_GOOGLE_CLIENT_ID= -e AKUS_GOOGLE_CLIENT_SECRET= \
  -e AKUS_GOOGLE_REDIRECT_URI= -e AKUS_SESSION_KEY= \
  api sh -c 'ruff check --no-cache apps/api && ruff format --check --no-cache apps/api && mypy --cache-dir=/tmp/akus-mypy --config-file apps/api/pyproject.toml apps/api/akus && alembic -c apps/api/alembic.ini upgrade head && alembic -c apps/api/alembic.ini check && pytest apps/api/tests -q -p no:cacheprovider'
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run format:check
npm --prefix apps/web test
npm --prefix apps/web run build
