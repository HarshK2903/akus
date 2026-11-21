#!/usr/bin/env bash
# Run the real scanner acceptance in a named, migrated QA database.
set -euo pipefail
cd "$(dirname "$0")/.."
database=${AKUS_TEST_DATABASE_NAME:-akus_system_audit_test}
[[ "$database" =~ ^akus_[a-z0-9_]+_test$ ]]
url="postgresql+psycopg://akus_demo:akus_demo@db:5432/$database"
stack=(docker compose -f compose.yaml -f compose.scanner.yaml)
"${stack[@]}" exec -T clamd clamdscan --version
"${stack[@]}" exec -T clamd clamdscan --ping=1
"${stack[@]}" run --rm --no-deps -v "$PWD/apps/api:/app/apps/api:ro" \
  -e AKUS_ENV=test -e AKUS_DEMO_ENABLED=true -e AKUS_PUBLIC_ORIGIN=http://127.0.0.1:5173 \
  -e "AKUS_DATABASE_URL=$url" -e "AKUS_TEST_DATABASE_URL=$url" \
  -e AKUS_GOOGLE_CLIENT_ID= -e AKUS_GOOGLE_CLIENT_SECRET= -e AKUS_GOOGLE_REDIRECT_URI= -e AKUS_SESSION_KEY= \
  api pytest -q -p no:cacheprovider apps/api/tests/clamd_acceptance.py
