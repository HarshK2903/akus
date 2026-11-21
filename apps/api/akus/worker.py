"""Durable quota reconciliation and local work ledger; no external email delivery."""

import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from akus.catalog import refresh_jobs
from akus.config import Settings
from akus.db import database
from akus.models import AuditEvent, WorkerHeartbeat, WorkJob
from akus.workspace import delivery


def tick(db: Session, job_id: UUID | None = None) -> bool:
    with db.begin():
        now = datetime.now(UTC)
        db.execute(
            insert(WorkerHeartbeat)
            .values(name="foundation", seen_at=now)
            .on_conflict_do_update(index_elements=["name"], set_={"seen_at": now})
        )
        candidates = select(WorkJob).where(
            WorkJob.state == "PENDING",
            WorkJob.kind != refresh_jobs.KIND,
            or_(WorkJob.next_attempt_at.is_(None), WorkJob.next_attempt_at <= now),
        )
        if job_id is not None:
            candidates = candidates.where(WorkJob.id == job_id)
        job = db.scalar(
            candidates.order_by(WorkJob.created_at).with_for_update(skip_locked=True).limit(1)
        )
        if job is None:
            return False
        job.attempts += 1
        job.next_attempt_at = None
        if job.kind in {"QUOTA_RECHECK", delivery.KIND}:
            from akus.applications.transfers import worker_recheck

            try:
                with db.begin_nested():
                    if job.kind == delivery.KIND:
                        delivery.archive(db, job)
                    else:
                        worker_recheck(db, UUID(job.key.split(":")[1]))
            except Exception as exc:
                job.last_error = type(exc).__name__[:90]
                if job.attempts % 3 == 0:
                    job.state = "DEAD"
                else:
                    job.next_attempt_at = now + timedelta(
                        seconds=10 * (2 ** ((job.attempts - 1) % 3))
                    )
                db.add(
                    AuditEvent(
                        action="WORK_FAILED",
                        details={
                            "job_id": str(job.id),
                            "attempt": str(job.attempts),
                            "error": job.last_error,
                            "state": job.state,
                        },
                    )
                )
            else:
                job.state = "DONE"
                job.last_error = None
        elif job.kind != "LOCAL_DEMO_BOOTSTRAP":
            job.state = "DEAD"
            db.add(AuditEvent(action="UNKNOWN_WORK_KIND", details={"job_id": str(job.id)}))
        else:
            job.state = "DONE"
            db.add(AuditEvent(action="LOCAL_DEMO_WORK_PROCESSED", details={"job_id": str(job.id)}))
        return True


def main() -> None:
    settings = Settings()
    engine, factory = database(settings.database_url)
    logging.basicConfig(level=logging.INFO)
    try:
        last_scan = -60.0
        while True:
            try:
                if time.monotonic() - last_scan >= 60:
                    from akus.exceptions.reviewer import notify_changes
                    from akus.exceptions.service import scan_due

                    with factory.begin() as db:
                        scan_due(db, settings)
                        notify_changes(db)
                    last_scan = time.monotonic()
                refresh_jobs.run_one(factory)
                for _ in range(20):
                    with factory() as db:
                        if not tick(db):
                            break
                else:
                    continue  # Backlog remains possible; start the next bounded batch immediately.
            except Exception as exc:
                logging.error("worker_tick_failed type=%s", type(exc).__name__)
            time.sleep(5)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
