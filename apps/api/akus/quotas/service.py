from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.catalog import common
from akus.catalog.models import Topic
from akus.catalog.schemas import QuotaWrite
from akus.models import AcademicYear
from akus.people.schemas import CommandResult
from akus.quotas.models import QuotaPool, QuotaRevision


def write_pool(
    db: Session, actor: Actor, key: UUID, department: UUID, body: QuotaWrite
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    office = common.require_hod(actor, department)
    op = f"QUOTA_DECISION:{department}"
    if result := common.replay(db, actor, key, op, body):
        return result
    if not db.get(Topic, body.topic_id) or not db.get(AcademicYear, body.academic_year_id):
        raise HTTPException(422, "CONFIGURED_TOPIC_AND_YEAR_REQUIRED")
    # Unique key protects simultaneous creation; published capacity never defaults.
    db.execute(
        insert(QuotaPool)
        .values(
            id=uuid4(),
            department_id=department,
            topic_id=body.topic_id,
            academic_year_id=body.academic_year_id,
            maximum=body.maximum,
            occupied=0,
            version=0,
            status="DRAFT",
        )
        .on_conflict_do_nothing(constraint="one_annual_shared_topic_pool")
    )
    pool = db.scalar(
        select(QuotaPool)
        .where(
            QuotaPool.department_id == department,
            QuotaPool.topic_id == body.topic_id,
            QuotaPool.academic_year_id == body.academic_year_id,
        )
        .with_for_update()
    )
    assert pool
    if pool.version != body.expected_version:
        raise HTTPException(409, "VERSION_CONFLICT")
    if body.maximum < pool.occupied:
        raise HTTPException(409, "CAP_BELOW_COUNTED_OCCUPANCY")
    if pool.status == "PUBLISHED" and not body.publish:
        raise HTTPException(409, "CANNOT_UNPUBLISH_QUOTA")
    before = pool.maximum if pool.version else None
    pool.maximum, pool.status, pool.version = (
        body.maximum,
        "PUBLISHED" if body.publish else "DRAFT",
        pool.version + 1,
    )
    if body.publish and not pool.published_at:
        pool.published_at = datetime.now(UTC)
    db.add(
        QuotaRevision(
            pool_id=pool.id,
            version=pool.version,
            previous_maximum=before,
            maximum=pool.maximum,
            status=pool.status,
            actor_id=actor.person.id,
            office_id=office.id,
            reason=body.reason,
            source_reference=body.source_reference,
        )
    )
    from akus.applications.service import queue_recheck

    queue_recheck(db)
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        pool.id,
        {
            "before_maximum": before,
            "maximum": pool.maximum,
            "status": pool.status,
            "office_id": str(office.id),
            "reason": body.reason,
        },
        department,
    )


def pool_view(db: Session, pool: QuotaPool) -> dict[str, Any]:
    topic, year = db.get(Topic, pool.topic_id), db.get(AcademicYear, pool.academic_year_id)
    return {
        "id": pool.id,
        "department_id": pool.department_id,
        "topic_id": pool.topic_id,
        "topic": topic.name if topic else None,
        "academic_year_id": pool.academic_year_id,
        "academic_year": year.label if year else None,
        "maximum": pool.maximum,
        "occupied": pool.occupied,
        "available": pool.maximum - pool.occupied if pool.status == "PUBLISHED" else None,
        "status": pool.status,
        "version": pool.version,
        "published_at": pool.published_at,
    }
