"""Durable quota reconciliation and local work ledger; no external email delivery."""

import logging
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from akus.config import Settings
from akus.db import database
from akus.models import AuditEvent, WorkerHeartbeat, WorkJob


def tick(db: Session, job_id: UUID | None = None) -> bool:
    with db.begin():
        now = datetime.now(UTC)
        db.execute(
            insert(WorkerHeartbeat)
            .values(name="foundation", seen_at=now)
            .on_conflict_do_update(index_elements=["name"], set_={"seen_at": now})
        )
        candidates = select(WorkJob).where(WorkJob.state == "PENDING")
        if job_id is not None:
            candidates = candidates.where(WorkJob.id == job_id)
        job = db.scalar(
            candidates.order_by(WorkJob.created_at).with_for_update(skip_locked=True).limit(1)
        )
        if job is None:
            return False
        if job.kind == "QUOTA_RECHECK":
            from akus.applications.transfers import worker_recheck

            worker_recheck(db, UUID(job.key.split(":")[1]))
            job.state = "DONE"
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
