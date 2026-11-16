# Local operations and future deployment

Start with README.md. Native local services: database 55432, API 8000, web 5173; Compose proxy 8080. Exact origin matters for CSRF. `scripts/dev.sh` migrates/seeds before starting API/worker/web and terminates its child processes on exit; database remains persistent. It never drops data. If a port is occupied, identify the process and select a distinct configured development environment; do not kill unrelated services.

Readiness `/api/v1/health/ready` verifies database connection, migration head and year-table query; liveness `/api/v1/health/live` remains available during database failure. A worker heartbeat older than 30 seconds is 'not reporting', not green. Request correlation IDs and safe JSON log fields help locate failures without logging token/body/credential values.

Migrations are forward-only. Run `alembic upgrade head`, then `alembic check`; schema modifications require a new migration. Seed only with `AKUS_DEMO_ENABLED=true`. Never repurpose a development fixture table as institutional staff data. Test database must end `_test`; no test truncates audit or drops schema.

Current worker only processes a local probe transaction; failed processing retries the polling loop, unknown kinds become DEAD. External delivery, leases/backoff/dead-letter UI, NPTEL adapter and Drive archives remain future work. Don't change a completed academic state based on job delivery status.

Production is disabled until institutional Google OIDC and effective authority are implemented. Before deployment, institution must supply approved domains, OIDC credentials via secret manager, staff source, calendar, privacy/retention terms, database least-privilege accounts, TLS, evidence storage, backup/PITR target and RPO/RTO. No deployment, external account changes or real credential access was performed.

Backup/restore procedure is not yet implemented or drilled. Phase 8 must prove PostgreSQL and private evidence restoration together, preserving immutable history; do not describe the local persistent volume as a backup. Ordinary July 1 rollover never resets occupancy; reschedule and historical reassessment follow active specification only.

## Phase 2A notes

Current migration head: `0003_office_scope`; PostgreSQL `btree_gist` is required (created by migration with the local migration account). Apply all migrations before starting the new API; readiness fails on the old head. Fresh install was separately verified on `akus_phase2a_fresh_test`; that isolated verification database is retained, not automatically dropped.

`seed_people` inserts missing deterministic LOCAL/DEMO facts and does not overwrite ended offices or changes. Source writes are real persisted transactions, even in demo mode. Do not end seeded officeholders simply to reset a demo; use a temporary source appointment and end that with its reason. Use a fresh isolated database if a pristine fixture set is needed; do not erase audit/receipts.

Source scanner preserves previous output: `python3 scripts/scan-source.py --report docs/qa/<new-report-name>.md`. It refuses to overwrite evidence. Current report is phase2a-secret-scan.md; original secret-scan.md is retained. This is a limited pattern check, not a complete security audit.
