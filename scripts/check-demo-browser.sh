#!/usr/bin/env bash
# Use the release web image and separate synthetic API, worker and database.
set -euo pipefail
cd "$(dirname "$0")/.."
db=${AKUS_BROWSER_TEST_DB:-akus_system_browser_test}
[[ "$db" =~ ^akus_[a-z0-9_]+_test$ ]]
origin=http://127.0.0.1:18086
name="akus-browser-audit-$$"
work=$(mktemp -d)
cleanup() {
  for service in proxy worker api; do
    docker stop "$name-$service" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT
exists=$(docker compose exec -T db psql -X -U akus_demo -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='$db'")
if [[ "$exists" != 1 ]]; then docker compose exec -T db createdb -U akus_demo "$db"; fi
settings=(--no-deps -e AKUS_ENV=test -e AKUS_DEMO_ENABLED=true -e "AKUS_PUBLIC_ORIGIN=$origin"
  -e "AKUS_DATABASE_URL=postgresql+psycopg://akus_demo:akus_demo@db:5432/$db"
  -e AKUS_GOOGLE_CLIENT_ID= -e AKUS_GOOGLE_CLIENT_SECRET= -e AKUS_GOOGLE_REDIRECT_URI= -e AKUS_SESSION_KEY=)
docker compose run --rm "${settings[@]}" migrate
for service in api worker; do
  docker compose run --rm -d --name "$name-$service" "${settings[@]}" "$service"
done
sed "s/reverse_proxy api:8000/reverse_proxy $name-api:8000/" infra/Caddyfile > "$work/Caddyfile"
docker compose run --no-deps --rm -d --name "$name-proxy" -p 127.0.0.1:18086:80 -v "$work/Caddyfile:/etc/caddy/Caddyfile:ro" proxy
curl --fail --retry 15 --retry-delay 1 --retry-all-errors -sS "$origin/api/v1/health/ready"
AKUS_E2E_URL="$origin" PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e -- "$@"
