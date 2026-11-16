#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
AKUS_PG_BIN="${AKUS_PG_BIN:-/usr/lib/postgresql/16/bin}"
mkdir -p .local
if [[ ! -f .local/postgres/PG_VERSION ]]; then
  "$AKUS_PG_BIN/initdb" -D .local/postgres --auth-local=trust --auth-host=trust --username=akus_demo --encoding=UTF8 --no-locale
fi
if ! "$AKUS_PG_BIN/pg_ctl" -D .local/postgres status >/dev/null 2>&1; then
  "$AKUS_PG_BIN/pg_ctl" -D .local/postgres -l .local/postgres.log -o '-h 127.0.0.1 -p 55432 -k /tmp' start
fi
for database in akus akus_test; do
  if ! "$AKUS_PG_BIN/psql" -h 127.0.0.1 -p 55432 -U akus_demo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$database'" | rg -q 1; then
    "$AKUS_PG_BIN/createdb" -h 127.0.0.1 -p 55432 -U akus_demo "$database"
  fi
done
