# Docker operations and future deployment

Use the existing Compose stack in README. Browser origin http://127.0.0.1:8080,
API /api/v1, docs /api/docs; database is not published. Build api/migrate/worker/web,
then `docker compose up -d`. The migrate job advances Alembic before API/worker start.
Current head `0021_application_files`; `python -m akus.startup` seeds only explicit
demo mode and skips fictional seed in institutional mode. Never delete/reset volumes.

Verify with `docker compose ps -a`, `docker compose logs --tail=30 migrate api`,
and GET /api/v1/health/ready. Readiness checks DB/schema; liveness is independent.
The worker page uses an actual heartbeat, not container state. A stale heartbeat marks worker health degraded. Use `docker compose stop` to stop while retaining data.

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
the worker rolls back failed quota effects and retries on a bounded schedule. Admin can inspect exhausted items in Worker operations. Email delivery requires external configuration. NPTEL metadata fetch is a bounded manual HTTPS call
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

## Phase 5 local verification and case handling

Use the existing Compose project. Forward upgrade runs in the migrate service on startup. Inspect the source identity of the named PostgreSQL volume, Alembic current/check, readiness, worker heartbeat, pool totals and transfer pairs. Preserve the volume and previous migrations.

For an official permanent departure, an authorized source operator finishes the dependent membership/teaching intervals and records the official exclusive episode end, then confirms the permanent order on that person's source page. The worker reconciles effective orders every minute. Verify the separate order date, optional exact instant, archive digest, observation time and record time in the case timeline. An ordinary leave or end date alone creates no separation release. The current department HoD uses the separation inbox for Q44/Q47. The office alerts page shows published cutoffs and vacancies to authorized oversight.

Integrity and historical review authorizations must refer to actual external formal designations. The operational database seeds none. For an authorized institutional handoff, retain the original order, identify the exact case, designated independent reviewer, purpose, optional authorized subject, basis and validity period. Revocations preserve the original appointment. Only the institution's controlled source process may provision such records. PostgreSQL test fixtures are synthetic and isolated. Browser actions still require ordinary login, current authority and CSRF protection.

Run the ordinary Docker regression gate with an isolated name ending in `_test`. Run the browser suite against the existing local port 8080. For the date-only enrollment, indeterminate separation and certificate reassessment form journeys, run `bash scripts/check-phase5-cases.sh` after building the current images. It launches temporary test API/proxy containers, uses a separately named retained PostgreSQL test database, serves the same compiled frontend on loopback port 18085 and stops those test containers on exit. The operational and test databases stay separate throughout.

For historical subject Silver, raw teaching rows, CSV files and case review appointments cannot resolve IO-02. An independently documented, previously adjudicated obligation in the source archive must match the same employment episode, canonical subject and original first assignment. Preserve the original authority basis, source decision, date and digest. The service never creates such source orders on behalf of a reviewer. An otherwise qualifying certificate stays pending for subject acceptance while its separately eligible annual assessment can proceed.

Run `docker compose exec -T db psql -U akus_demo -d akus < scripts/verify-quota.sql` for a consistent read-only snapshot. The mismatch counters should be zero. Run the same SQL on the isolated departures test database to inspect populated separation and invalidation cases. The output includes the migration head, transfer movement count and application state counts.

When a transfer is waiting for a missing, unpublished or full pool, check the specific destination year, department and canonical topic and its published capacity. Qualifying capacity changes queue only affected transfers. Replaying a work item revalidates the current allocation and case before moving a seat.


## Phase 8 release and recovery

Build all six services with their release Dockerfiles, then run `docker compose up -d --no-build --wait`. Check the migrate exit status, API readiness, worker heartbeat and mounted PostgreSQL volume. Application images can be redeployed independently of storage. Forward-only schema changes require a compatible image. Record the volume identity and migration head before release.

Use a quiescent, synthetic acceptance database to practice restoration. Run `bash scripts/check-test-restore.sh akus_phase8_release_test akus_phase8_restore_test` with an unused target name. The script streams a PostgreSQL custom-format dump into a new database, restores schema, constraints, private evidence and audit rows, compares counts and ordered file manifests and runs all four reconciliation scripts. Review each discrepancy counter. It retains both databases. Choose another new name for a subsequent rehearsal. A failed rehearsal leaves the target available for inspection.

Institutional operations require a separately approved encrypted backup destination, access-controlled credentials and a tested key-recovery process. Schedule consistent PostgreSQL backups including evidence bytes and immutable events. Keep authentication settings and keys in the approved secret manager. Record actual restore times, reconcile document digests and quota/compliance ledgers, restrict restored copies to the recovery team and rotate active session credentials before opening a recovered installation to users. Define retention, RPO/RTO and WAL/PITR settings with the institution. Rehearsing a local synthetic restore validates the application schema and data path.

Monitor API readiness and latency, database capacity, heartbeat age, queue attempts, oldest pending case, quota discrepancies and provider failures. Metadata workers claim a bounded lease, release the transaction for the HTTPS request, then recheck the original Admin authority and lease before recording an observation. A failed fetch retains its failure evidence. Three failed attempts reach the dead queue. Inspect the original request and source before authorizing a retry. A provider outage never supplies a certificate, enrollment date or replacement exam date.

The local Compose configuration binds the browser to loopback and uses demonstration database credentials. Institutional deployment needs a ratified hostname and TLS, a separate provisioned PostgreSQL runtime role, operator-controlled migrations, secret storage, a tested malware-scanning pipeline, authorized private evidence processing, and approved external identity/client configuration. Configure and exercise these in the institution's own environment before launch.

Migration 0021 adds immutable private PDF revision storage. Previous submissions retain their original evidence snapshots. The authorized owner can download clean bytes only. Configure the private clamd socket before performing scanner acceptance. Pending scans stay quarantined.

Run `python3 scripts/check-consistency.py akus` after migration. For a restore drill, pass the restored test database name as well. It runs read-only transactions and exits nonzero if a discrepancy is present or an expected counter is missing. The output contains aggregate counts.

## Full-system acceptance rehearsal

Use the existing Compose project. Verify the current database name, loopback public origin, schema revision and volume identity before starting. Record the Git HEAD and local changes. Take a private logical backup with a restricted filesystem mode and verify its archive catalog. Protect and retain the backup according to institutional instructions.

1. Build the current images with `docker compose build api migrate worker web proxy db`. Start with `docker compose up -d --no-build --wait`. Check the migration exit, ready endpoint and worker heartbeat separately.
2. Run `AKUS_TEST_DATABASE_NAME=akus_system_audit_test bash scripts/check-docker.sh`. This gate applies migrations to a test database, checks for drift and exercises PostgreSQL, Python, frontend and the production web build.
3. Run `bash scripts/check-demo-browser.sh` to exercise the compiled web UI on port 18086 with a dedicated local demo API, worker and PostgreSQL test database. Run `bash scripts/check-demo-browser.sh --config record-audit.config.ts` after the standard suite has created its synthetic case records. Run `bash scripts/check-phase5-cases.sh` for the four case-appointed/HR journeys on port 18085. Serialize the browser suites. Archive existing screenshot evidence before running because the historical journeys use fixed output names.
4. Run `python3 scripts/check-consistency.py` with the explicit database names from the rehearsal. For backup recovery use `bash scripts/check-test-restore.sh SOURCE_TEST_DB NEW_DESTINATION_TEST_DB` on quiescent synthetic data. The destination must be new. Compare both manifests, every discrepancy counter and the exit status. Keep the source and restored databases. Treat operational backup restore, retention, timing and access as separate deployment gates.

See the [acceptance report](qa/FINAL_ACCEPTANCE_REPORT.md) for dated evidence and the [release gate](qa/RELEASE_READINESS_GATE.md) for operator-owned decisions.

## Recover an interrupted acceptance run

Read the last combined log through the final Vite build, and check the standard, isolated and record-page browser summaries separately. Check remaining disk space. If the services have stopped, confirm the retained volume and PostgreSQL cluster identity, start the existing database and take a mode-0600 logical backup in a private directory with durable storage. Inspect its archive catalog. Start the remaining Compose services, then verify the migration exit, HTTP readiness and worker heartbeat. Reconcile the named databases again after the last synthetic writer finishes.

The DB image extends official PostgreSQL 16 with a vendor zlib update. The web and proxy share the Caddy base with vendor SSL and zlib patches. The API installs its locked dependencies at build time and drops the pip installer before running as UID 65532. To assess release images, export image layers locally, keep runtime volumes outside the scan, compare before/after package findings and record both upstream residuals and known fixed versions. Approve any database major upgrade separately. [Image advisory inventory](qa/system-audit-image-advisories.md) · [Acceptance checklist](qa/FINAL_AUDIT_CHECKLIST.md)

### Approved evidence scanner

When an authorized local clamd service exists, set `AKUS_CLAMD_DIR` to its dedicated socket directory and `AKUS_CLAMD_GID` to the numeric group permitted to connect. The socket filename inside that directory must be `clamd.sock`. Keep other services’ sockets and private files outside this directory. Validate with `docker compose -f compose.yaml -f compose.clamd.yaml config --quiet`. Use both files for the scanner-enabled API lifecycle. The override bind-mounts the directory read-only, adds the required supplementary group and refuses to create a missing host directory. Installing and maintaining signatures and verifying clean, rejected and outage paths against the actual engine are operator acceptance actions. Existing quarantined evidence retains its recorded scan result. An authorized owner can submit a new revision when the service becomes available.

### Local scanner deployment and acceptance

From the repository root, use both Compose files throughout the scanner-enabled API lifecycle. The Debian PostgreSQL image and its volume are independent of the scanner's Alpine packages and signature volume.

```sh
docker compose -f compose.yaml -f compose.scanner.yaml config -q
docker compose -f compose.yaml -f compose.scanner.yaml build clamd api
docker compose -f compose.yaml -f compose.scanner.yaml up -d --no-deps --wait clamd api
docker compose -f compose.yaml -f compose.scanner.yaml exec -T clamd clamdscan --version
docker compose -f compose.yaml -f compose.scanner.yaml exec -T clamd clamdscan --ping=1
AKUS_TEST_DATABASE_NAME=akus_system_audit_test bash scripts/check-clamd.sh
```

The last command requires a migrated synthetic database ending in `_test`. It creates synthetic acceptance records. The vendor image ships signed definitions. FreshClam checks for updates twelve times per day. The daemon only listens on the Unix socket and shares its dedicated socket directory with the non-root API. The scanner has its own outbound network, and receives uploaded bytes through INSTREAM. It has no database credentials or evidence-directory mount. The host-provided socket overlay remains available as a separate deployment option. Configure such a daemon to report timestamps in UTC.

The API requires an exact clean response plus a parseable signature database serial and a timestamp no older than seven days. Failed scans quarantine the upload, and detected files are rejected. The seven-day window is a local operational safety bound. The institution should set its production update and monitoring SLA. A saved clean verdict describes the bytes at scan time. A quarantined owner can submit a new revision. Certificate assertions keep the original immutable bytes and record the new scan status, engine and definition version on the new event. A person still needs an authorized independent academic verification to earn credit.

Monitor the actual daemon and definition age, FreshClam update failures, API quarantine rates and storage. Size the production service for concurrent updates and scans and approve its network egress. Rehearse recovery and verify both positive and negative paths after each image change. [ClamAV deployment guidance](https://docs.clamav.net/manual/Installing/Docker.html) · [Local acceptance](qa/remediation-final-scanner.txt)

After the real-engine tests, verify the compiled UI using the same synthetic database. The additional Playwright case signs in through the existing demo flow, retrieves the PDF via the visible clean-revision link, checks its digest and checks access from a different role.

```sh
COMPOSE_FILE="$PWD/compose.yaml:$PWD/compose.scanner.yaml" \
  AKUS_BROWSER_TEST_DB=akus_system_audit_test \
  bash scripts/check-demo-browser.sh --config scanner.config.ts
```
