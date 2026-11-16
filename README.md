# AKUS | NPTEL

Phase 2A working staff and effective-office source workflows; Phase 2 remains in progress. React 19 / TypeScript / Vite / React Router / TanStack Query, FastAPI on Python 3.13, synchronous SQLAlchemy / Psycopg 3, PostgreSQL 16 and Alembic. Uses the binding V2.4 specification in `docs/spec/AKUS_MASTER_SPEC.txt`.

Working: fictional local sessions backed by explicit people/employment/office records, staff creation/search/history, office creation/end/history, current server authorization, scoped/read-only pages, policy search, database-backed years, health and local worker. Full institutional workflows are scheduled for Phases 2–8. No Google OIDC or NPTEL verification is simulated as genuine.

## Native development (verified)

Prerequisites: Python 3.13, Node 24/npm, PostgreSQL 16 server/client binaries. On a pyenv host use `pyenv install 3.13.7` if needed; `.python-version` selects it. No system Python changes are needed.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r apps/api/requirements.lock
.venv/bin/pip install --no-deps -e apps/api
npm --prefix apps/web ci --no-audit --no-fund
scripts/dev-db.sh
scripts/dev.sh
```

`dev-db.sh` initializes an isolated ignored `.local/postgres` cluster only if absent, binds loopback port 55432 and creates `akus` and `akus_test` only if missing. It uses local trust authentication for this fictional development cluster; do not put real data in it or expose it beyond loopback. Override `AKUS_PG_BIN` if PostgreSQL binaries are elsewhere. It does not stop, drop or alter other clusters. Database remains running when the web process stops.

Open **http://127.0.0.1:5173**. Use that exact origin (localhost is a different origin). API docs: http://127.0.0.1:8000/api/docs. Readiness: http://127.0.0.1:8000/api/v1/health/ready. Frontend `/api` requests proxy to the API. API configuration uses `AKUS_` environment variables; see `.env.example`. Scripts explicitly enable demo mode, which is otherwise disabled by default.

Choose a fictional identity at sign-in: Mira Rao (Faculty), Arun Sen (DRC Head), Leela Iyer (HoD), Dev Mehta (Principal), Nila Shah (Admin), Omar Das (acting HoD). All are LOCAL/DEMO records; no real institutional or provider facts. Fictional source-shaped office grants exercise the actual authorization services. DRC and HoD fixtures are distinct people. Admin can record staff/offices; Principal reads source records globally; HoD reads current department scope; Faculty/DRC read self. Demo role labels themselves grant nothing.

Source workflow: choose Nila Shah → Staff directory → Add staff record → save → Record appointment → Office appointments → View appointment → confirm end. Inspect immutable staff history. See `docs/USER_MANUAL.md` for source prerequisites and read-only role examples.

Foundation demo: enter workspace → see live service status and PostgreSQL years → Profile & access → Policy guide → search `P-51` → reload to retain search → sign out. Use a narrow viewport and the menu to navigate by keyboard. No quota/application buttons exist yet.

## Verification

```bash
scripts/check.sh
# Start scripts/dev.sh in another terminal before browser tests.
cd apps/web
PLAYWRIGHT_BROWSERS_PATH="$PWD/../../.local/browsers" npx playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/../../.local/browsers" npm run e2e
```

Tests use a separate database ending `_test`. Never point them at institution data. `scripts/check.sh` runs Ruff, mypy, migrations, drift check, PostgreSQL pytest, ESLint, TypeScript, Vitest and Vite build. Browser suite uses Chromium, real API navigation and axe, and writes responsive screenshots to `docs/qa/`. CI definition is included; remote CI has not been run in this session.

Refresh API types after contract changes:

```bash
.venv/bin/python scripts/export-openapi.py
npm --prefix apps/web run api:types
```

Python exact tested dependencies are in `apps/api/requirements.lock`; npm dependencies are in `apps/web/package-lock.json`. Migrations (current head `0003_office_scope`) are forward-only to protect audit history. Do not downgrade/drop an existing database; apply additive migrations or follow an approved restore procedure.

## Compose alternative

```bash
docker compose up --build
```

Open http://127.0.0.1:8080. Compose includes PostgreSQL, a migration/seed job, API, worker, compiled web and same-origin Caddy proxy. Only the proxy port is published, on loopback. Credentials in this local manifest are conspicuously fictional. Compose was built and booted from fresh containers, with successful migrations, healthy API/database and HTTP 200 through Caddy; see TEST_RESULTS.md for browser verification. Production startup deliberately rejects configuration until Phase 2 identity/access is implemented. No production deployment is authorized or claimed.

## Persistent handoff

Read `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/implementation-plan.md`, `docs/traceability.md`, `docs/POLICY_REGISTER.md`, `POLICY_GAPS.md` and `docs/route-matrix.md`. All 80 route contracts and Q01–Q50 are inventoried; inventory is not implementation coverage. The next slice is **Phase 2B: institutional identity and account linking**, following `docs/codex/BUILD_PHASES.md`.

To verify the compiled Compose build with the browser suite, set `AKUS_E2E_URL=http://127.0.0.1:8080` alongside `PLAYWRIGHT_BROWSERS_PATH` when running `npm run e2e` in `apps/web`. See TEST_RESULTS.md for the current native and compiled Compose results, including source actions and live authority revocation.

Stopping local services without deleting data: Ctrl+C in the native dev terminal, `docker compose stop` for containers, and `/usr/lib/postgresql/16/bin/pg_ctl -D .local/postgres stop` for the isolated native database. Do not remove database volumes as a routine stop procedure.
