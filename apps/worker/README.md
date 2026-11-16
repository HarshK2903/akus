# PostgreSQL worker

Entry point: `python -m akus.worker`, shared package `apps/api/akus/worker.py`.
Phase 1 processes a local bootstrap event and heartbeat with row locking / SKIP LOCKED, one transaction and immutable audit. Unknown job types become DEAD. No email, provider validation or Drive delivery is claimed. Later slices add leases, retry/backoff and external idempotency before introducing external side effects.
