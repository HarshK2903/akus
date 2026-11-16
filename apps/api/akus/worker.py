"""Phase 1 local work-ledger probe; external delivery adapters are future work."""

import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from akus.config import Settings
from akus.db import database
from akus.models import AuditEvent, WorkerHeartbeat, WorkJob


def tick(db: Session) -> bool:
    with db.begin():
        now = datetime.now(UTC)
        db.execute(
            insert(WorkerHeartbeat)
            .values(name="foundation", seen_at=now)
            .on_conflict_do_update(index_elements=["name"], set_={"seen_at": now})
        )
        job = db.scalar(
            select(WorkJob)
            .where(WorkJob.state == "PENDING")
            .order_by(WorkJob.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return False
        if job.kind != "LOCAL_DEMO_BOOTSTRAP":
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
        while True:
            try:
                with factory() as db:
                    tick(db)
            except Exception as exc:
                logging.error("worker_tick_failed type=%s", type(exc).__name__)
            time.sleep(5)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
