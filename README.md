# AKUS | NPTEL

React 19/TypeScript/Vite, FastAPI/Python 3.13, synchronous SQLAlchemy/Psycopg 3,
PostgreSQL 16 and Alembic. Binding specification: docs/spec/AKUS_MASTER_SPEC.txt.

The local application supports staff imports and source corrections, effective-dated offices,
NPTEL catalog and topic governance, annual quota reservations and transfers, DRC/HoD reviews,
employment history, certificate evidence, annual compliance and subject-wise Silver reporting.
The five workspaces use role-scoped tasks, notifications, search and reports. The running
dataset is explicitly LOCAL/DEMO. Live institutional Google sign-in requires approved OAuth
configuration, staff records and voluntary account-holder participation. Certificate authenticity
and unresolved institutional decisions retain their individual verification states.
[Phase 8 checklist](docs/codex/PHASE8_CHECKLIST.md) · [Test evidence](TEST_RESULTS.md) · [Open policies](POLICY_GAPS.md)

## Existing Docker application

```sh
docker compose config -q
docker compose build api migrate worker web proxy db
docker compose up -d
```

Open **http://127.0.0.1:8080**; API docs **http://127.0.0.1:8080/api/docs**;
readiness **http://127.0.0.1:8080/api/v1/health/ready**. Use this exact origin for CSRF.
Compose runs PostgreSQL, forward migration/startup job, API, worker, compiled React
web and Caddy proxy. Only the loopback proxy port is published. Current migration
head is `0021_application_files`. Existing volume `akus-local_akus_pg` is retained.
`docker compose stop` stops services without deleting data. Never use down -v/reset.

Default Compose settings are fictional demo data and credentials. Choose Nila Shah
(Admin) to import/correct sources and manage teaching; Mira Rao (Faculty), Arun Sen
(DRC Head), Leela Iyer (HoD), Dev Mehta (Principal), Omar Das (acting HoD) demonstrate
current source permissions. These are not the five real UAT accounts. Demo role labels
never grant authority. Created source/audit records persist across restarts.

Full local walkthrough and import columns: [docs/USER_MANUAL.md](docs/USER_MANUAL.md).
Google setup, exact callback, approved roster, bootstrap/revocation and five-participant
UAT: [docs/GOOGLE_OIDC_SETUP.md](docs/GOOGLE_OIDC_SETUP.md). Use a private ignored `.env`;
never paste secrets into chat. Do not enable demo mode in the real institutional dataset.

## Verification

Host quality tooling requires Node 24/npm; Python 3.13 virtualenv is used for contract
export and optional developer tooling. Application services remain Docker-based.

```sh
npm --prefix apps/web ci --no-audit --no-fund
scripts/check-docker.sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web exec -- playwright install chromium
AKUS_E2E_URL=http://127.0.0.1:8080 PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e
```

The Docker gate creates `akus_completion_test` only if missing and runs Ruff, format,
mypy, migrations/drift and PostgreSQL tests in that isolated database, then frontend
lint/type/format/unit/build. It never resets the app database. Browser actions use
explicit fictional data in the LOCAL/DEMO app and preserve audit history. Do not run
these browser fixtures against an institutional deployment. Screenshots/logs: docs/qa.
Remote CI has not been executed in this session.

Refresh API contracts after API changes:

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/export-openapi.py
npm --prefix apps/web run api:types
```

Exact dependencies: apps/api/requirements.lock and apps/web/package-lock.json.
Prior native development scripts remain for existing users, but this continuation
uses the established Docker app and does not start a second native stack. Native
ports/instructions in historical QA records are not current runtime claims.

## Resume safely

Read AGENTS.md, the master specification, [approved build phases](docs/codex/BUILD_PHASES.md),
[Phase 8 instructions](docs/codex/PHASE8_CONTINUATION.md), [Phase 8 checklist](docs/codex/PHASE8_CHECKLIST.md),
[build progress](BUILD_PROGRESS.md) and [test results](TEST_RESULTS.md). Check Git changes, running services
and the stored QA logs before repeating a migration or test. The [traceability matrix](docs/traceability.md)
maps the 80 target routes. [Policy gaps](POLICY_GAPS.md) and the Google UAT guide track the remaining
institutional decisions and external acceptance work.
