#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# An additional pair of short-lived test containers serves the compiled UI on a
# loopback-only port. Every academic mutation targets an isolated test database.
work=$(mktemp -d)
name="akus-phase5-proof-$$"
origin=http://127.0.0.1:18085
cleanup() {
  for instance in "$name-proxy" "$name-api"; do
    docker stop "$instance" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT
docker compose run --rm --no-deps -v "$PWD/apps/api:/app/apps/api:ro" -e AKUS_ENV=test \
  -e AKUS_DEMO_ENABLED=true -e AKUS_PUBLIC_ORIGIN=http://127.0.0.1:5173 \
  -e AKUS_TEST_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/akus_phase5_browser_test \
  -e AKUS_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/akus_phase5_browser_test \
  api pytest -sq -p no:cacheprovider apps/api/tests/test_exception_cases.py::test_unresolved_same_day_chronology_and_unassessed_certificate_are_recoverable apps/api/tests/test_compliance.py::test_isolated_appointed_browser_fixture | tee "$work/fixture.log"
fixture=$(sed -n 's/^LOCAL_PHASE5_BROWSER=//p' "$work/fixture.log")
test -n "$fixture"
credential=$(sed -n 's/^\.*LOCAL_PHASE6_BROWSER=//p' "$work/fixture.log")
test -n "$credential"
docker compose run --no-deps --rm -d --name "$name-api" -e AKUS_ENV=test -e AKUS_DEMO_ENABLED=true \
  -e AKUS_PUBLIC_ORIGIN="$origin" -e AKUS_GOOGLE_CLIENT_ID= -e AKUS_GOOGLE_CLIENT_SECRET= \
  -e AKUS_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/akus_phase5_browser_departures_test api
sed "s/reverse_proxy api:8000/reverse_proxy $name-api:8000/" infra/Caddyfile > "$work/Caddyfile"
docker compose run --no-deps --rm -d --name "$name-proxy" -p 127.0.0.1:18085:80 -v "$work/Caddyfile:/etc/caddy/Caddyfile:ro" proxy
curl --fail --retry 15 --retry-delay 1 --retry-all-errors --silent --show-error "$origin/api/v1/health/ready"
AKUS_PHASE5_FIXTURE="$fixture" AKUS_PHASE6_FIXTURE="$credential" AKUS_E2E_URL="$origin" PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" \
  npm --prefix apps/web run e2e -- --config phase5-proof.config.ts
