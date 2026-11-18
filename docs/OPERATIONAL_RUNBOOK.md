# Docker operations and future deployment

Use the existing Compose stack in README. Browser origin http://127.0.0.1:8080,
API /api/v1, docs /api/docs; database is not published. Build api/migrate/worker/web,
then `docker compose up -d`. The migrate job advances Alembic before API/worker start.
Current head `0010_personal_schedule`; `python -m akus.startup` seeds only explicit
demo mode and skips fictional seed in institutional mode. Never delete/reset volumes.

Verify with `docker compose ps -a`, `docker compose logs --tail=30 migrate api`,
and GET /api/v1/health/ready. Readiness checks DB/schema; liveness is independent.
The worker page uses an actual heartbeat, not container state. A stale heartbeat
is not green. Use `docker compose stop` to stop while retaining data.

Migrations are forward-only. 0004–0006 add identity/source storage and preserve
existing office/audit facts; 0005 backfills immutable source snapshots and allows
controlled supersession. btree_gist is required. Existing data upgrade and a new
isolated `akus_phase2_completion_fresh_test` database both passed migration/drift;
repeat demo seeding passed. Test databases are retained. `scripts/check-docker.sh`
uses a separate name ending `_test`, never resets/truncates source or audit history.

Demo seed inserts missing deterministic fixtures without rewriting ended offices.
Source actions remain real persisted transactions. Browser tests create labeled
synthetic sources and end only their own temporary appointments with audit reasons.
Never reset officeholders or delete audit to obtain a prettier demo.

Institutional setup and operator-only Admin bootstrap/revocation are documented in
GOOGLE_OIDC_SETUP.md. Private .env fields must never appear in logs or chat. Use
`docker compose config -q`, not an expanded configuration dump. Avoid inspecting
container environments once secrets exist. API access logs are disabled so callback
codes cannot enter query-string logs; structured request logs contain no query/body.
No provider token is stored. Keep live UAT separate from the demo database, with demo
disabled and approved roster facts. An email string is not ownership or office proof.

Source history/audit and external identity facts are immutable under DB triggers.
Direct database administrators still control the DB; this is not a substitute for
least-privilege runtime accounts. Phase 8 must verify TLS, production secrets,
retention/monitoring, runtime DB privileges, private evidence storage and backup/PITR
with an actual restore drill. The current named volume is not a backup.

The worker handles LOCAL_DEMO_BOOTSTRAP and durable QUOTA_RECHECK jobs with row locks
and SKIP LOCKED. Publication/release/source changes queue affected applications; each
recheck revalidates the current allocation and capacity. Unknown kinds become DEAD;
exceptions roll back and retry. External email delivery and advanced retry/dead-letter
administration remain future work. NPTEL metadata fetch is a bounded manual HTTPS call
outside transactions; see NPTEL_PROVIDER_SETUP.md. July rollover never resets quota.
Verified reschedules use atomic balanced transfer or retain counted source plus case.

Source pattern scanner preserves prior evidence:
`python3 scripts/scan-source.py --report docs/qa/<new-report-name>.md`.
It is a limited pattern check, not comprehensive security certification.

Source inventory check without rewriting files: `python3 scripts/spec_inventory.py --check`.
Regeneration preserves the hand-maintained Phase 2 policy continuation;
`scripts/traceability.py` records current source proof separately from planned academics.

Phase 3 forward migrations 0007–0010 add catalog/mapping/annual pools, application
ledger/deferred count guards, permanent quota keys/balanced transfer pairs and personal
schedule evidence binding. Current existing database and a separate fresh database
passed Alembic current/check; durable evidence: qa/phase3-fresh-migrations.txt.
Never rewrite applied migrations; correct invariants through a new additive revision.
