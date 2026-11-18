"""Verified schedule changes never alter the original submission or charging topic."""

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from akus.access import Actor
from akus.applications import service
from akus.applications.models import Allocation, Application, Ledger, Reconciliation
from akus.applications.personal_schedule import current as personal_schedule
from akus.applications.schemas import Recheck
from akus.catalog import common
from akus.catalog.models import AcademicEvent, Offering, ProviderSnapshot
from akus.catalog.service import snapshot
from akus.models import AcademicYear, AuditEvent
from akus.people.schemas import CommandResult
from akus.quotas.models import QuotaPool


def record(
    db: Session, app: Application, actor: Actor | None, kind: str, facts: dict[str, Any]
) -> None:
    if actor:
        common.event(db, actor, app.id, kind, facts, app.department_id)
    else:
        db.add(
            AcademicEvent(
                entity_id=app.id,
                kind=kind,
                department_id=app.department_id,
                actor_id=None,
                data=facts,
            )
        )
        db.add(
            AuditEvent(
                action=kind,
                details={
                    "application_id": str(app.id),
                    "process": "VERIFIED_SCHEDULE_RECONCILER",
                    "policy": "V2.3",
                },
            )
        )
    service.notice(db, app, kind, facts)


def reconcile(
    db: Session, app: Application, offering: Offering, actor: Actor | None = None
) -> None:
    allocation = db.get(Allocation, app.id)
    if not allocation or allocation.state == "RELEASED":
        service.resolve_released_cases(db, app)
        return
    source = snapshot(db, offering)
    verified_personal = personal_schedule(db, app.id)
    if not source or (offering.source_status != "CURRENT" and not verified_personal):
        service.case(
            db,
            app,
            "QUOTA_TRANSFER",
            "VERIFIED_SCHEDULE_UNAVAILABLE",
            {},
            source.id if source else None,
        )
        return
    personal = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == app.id,
            Reconciliation.kind == "PERSON_SCHEDULE",
            Reconciliation.status == "OPEN",
        )
    )
    if personal:
        # The confirmed policy demands person applicability. An asserted hall ticket
        # cannot be promoted to verified by Admin/HoD rank or a global provider feed.
        service.case(
            db,
            app,
            "QUOTA_TRANSFER",
            "PERSON_SPECIFIC_SCHEDULE_REVIEW_PENDING",
            {
                "person_schedule_case_id": str(personal.id),
                "source_pool_id": str(allocation.pool_id),
            },
            source.id,
        )
        return
    old_schedule = db.get(ProviderSnapshot, allocation.schedule_snapshot_id)
    if not verified_personal and old_schedule and source.observed_at < old_schedule.observed_at:
        return
    scheduled = (
        verified_personal.scheduled_exam_on.isoformat()
        if verified_personal
        else source.metadata_json.get("scheduled_exam_on")
    )
    personal_id = verified_personal.id if verified_personal else None
    if allocation.state == "RETAINED":
        if old_schedule and old_schedule.metadata_json.get("scheduled_exam_on") != scheduled:
            service.case(
                db, app, "QUOTA_TRANSFER", "TERMINAL_RETAINED_POLICY_PENDING", {}, source.id
            )
        return
    if not service.applicant_still_eligible(db, app):
        service.case(
            db, app, "SOURCE_TRANSITION", "APPLICANT_SOURCE_CHANGE_POLICY_PENDING", {}, source.id
        )
        return
    service.resolve_case(db, app, "SOURCE_TRANSITION", "CURRENT_SOURCE_ELIGIBLE")
    year = (
        db.scalar(
            select(AcademicYear).where(
                AcademicYear.starts_on <= date.fromisoformat(scheduled),
                AcademicYear.ends_on >= date.fromisoformat(scheduled),
            )
        )
        if scheduled
        else None
    )
    current = db.get(QuotaPool, allocation.pool_id)
    assert current
    if year and current.academic_year_id == year.id:
        if (
            allocation.schedule_snapshot_id != source.id
            or allocation.personal_schedule_id != personal_id
        ):
            allocation.schedule_snapshot_id, allocation.version = source.id, allocation.version + 1
            allocation.personal_schedule_id = personal_id
            record(
                db,
                app,
                actor,
                "SCHEDULE_RECONFIRMED",
                {
                    "snapshot_id": str(source.id),
                    "scheduled_exam_on": scheduled,
                    "pool_id": str(current.id),
                    "movement": "NONE_SAME_YEAR",
                    "personal_schedule_id": str(personal_id) if personal_id else None,
                },
            )
        service.resolve_case(db, app, "QUOTA_TRANSFER", "CURRENT_YEAR_MATCHES")
        return
    target = (
        db.scalar(
            select(QuotaPool).where(
                QuotaPool.department_id == current.department_id,
                QuotaPool.topic_id == current.topic_id,
                QuotaPool.academic_year_id == year.id,
            )
        )
        if year
        else None
    )
    pool_ids = [current.id] + ([target.id] if target else [])
    locked = {
        p.id: p
        for p in db.scalars(
            select(QuotaPool)
            .where(QuotaPool.id.in_(pool_ids))
            .order_by(QuotaPool.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    }
    current, target = locked[current.id], locked[target.id] if target else None
    reason = (
        "TARGET_YEAR_NOT_CONFIGURED"
        if not year
        else "TARGET_QUOTA_MISSING"
        if not target
        else "TARGET_QUOTA_UNPUBLISHED"
        if target.status != "PUBLISHED"
        else "TARGET_QUOTA_FULL"
        if target.occupied >= target.maximum
        else None
    )
    facts = {
        "source_pool_id": str(current.id),
        "target_pool_id": str(target.id) if target else None,
        "target_year": year.label if year else None,
        "scheduled_exam_on": scheduled,
        "snapshot_id": str(source.id),
        "topic_id": str(current.topic_id),
        "personal_schedule_id": str(personal_id) if personal_id else None,
    }
    if reason:
        service.case(db, app, "QUOTA_TRANSFER", reason, facts, source.id)
        return
    assert target
    movement = uuid4()
    current.occupied -= 1
    target.occupied += 1
    allocation.pool_id, allocation.schedule_snapshot_id, allocation.version = (
        target.id,
        source.id,
        allocation.version + 1,
    )
    allocation.personal_schedule_id = personal_id
    for pool, delta in [(current, -1), (target, 1)]:
        db.add(
            Ledger(
                movement_id=movement,
                application_id=app.id,
                pool_id=pool.id,
                delta=delta,
                kind="TRANSFER",
                personal_schedule_id=personal_id,
                snapshot_id=source.id,
                actor_id=actor.person.id if actor else None,
            )
        )
    service.resolve_case(db, app, "QUOTA_TRANSFER", "TRANSFERRED")
    record(
        db,
        app,
        actor,
        "QUOTA_TRANSFERRED",
        facts | {"movement_id": str(movement), "policy": "V2.3"},
    )
    service.queue_recheck(db)


def schedule_accepted(db: Session, offering: Offering, actor: Actor) -> None:
    # Caller holds the offering exclusively, so no submission/closure can interleave.
    db.flush()
    apps = list(
        db.scalars(
            select(Application)
            .where(Application.offering_id == offering.id, Application.state != "DRAFT")
            .order_by(Application.id)
            .with_for_update()
        )
    )
    # An offering event may affect several departments/topics. Prelock the union
    # of current and potential target pools globally before any movement.
    source = snapshot(db, offering)
    scheduled = source.metadata_json.get("scheduled_exam_on") if source else None
    year = (
        db.scalar(
            select(AcademicYear).where(
                AcademicYear.starts_on <= date.fromisoformat(scheduled),
                AcademicYear.ends_on >= date.fromisoformat(scheduled),
            )
        )
        if scheduled
        else None
    )
    pool_ids = set()
    for app in apps:
        allocation = db.get(Allocation, app.id)
        if not allocation or allocation.state == "RELEASED":
            continue
        current = db.get(QuotaPool, allocation.pool_id)
        assert current
        pool_ids.add(current.id)
        personal = personal_schedule(db, app.id)
        target_year = (
            db.scalar(
                select(AcademicYear).where(
                    AcademicYear.starts_on <= personal.scheduled_exam_on,
                    AcademicYear.ends_on >= personal.scheduled_exam_on,
                )
            )
            if personal
            else year
        )
        if target_year:
            target = db.scalar(
                select(QuotaPool).where(
                    QuotaPool.department_id == current.department_id,
                    QuotaPool.topic_id == current.topic_id,
                    QuotaPool.academic_year_id == target_year.id,
                )
            )
            if target:
                pool_ids.add(target.id)
    list(
        db.scalars(
            select(QuotaPool)
            .where(QuotaPool.id.in_(pool_ids))
            .order_by(QuotaPool.id)
            .with_for_update()
        )
    )
    for app in apps:
        reconcile(db, app, offering, actor)


def manual(db: Session, actor: Actor, key: UUID, app_id: UUID, body: Recheck) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, offering = service.lock_application(db, app_id, actor)
    common.require_hod(actor, app.department_id)
    op = f"QUOTA_RECHECK:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    reconcile(db, app, offering, actor)
    return common.finish(
        db, actor, key, op, body, app.id, body.model_dump(mode="json"), app.department_id
    )


def mapping_changed(db: Session, department: UUID, course: UUID) -> None:
    # No application lock while holding mapping anchor: use durable post-commit work.
    from akus.models import WorkJob

    for app_id in db.scalars(
        select(Application.id).where(
            Application.department_id == department,
            Application.course_id == course,
            Application.state != "DRAFT",
        )
    ):
        db.add(WorkJob(key=f"recheck:{app_id}:{uuid4()}", kind="QUOTA_RECHECK", state="PENDING"))


def worker_recheck(db: Session, app_id: UUID) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock_shared(8210402)"))
    app, offering = service.lock_application(db, app_id)
    reconcile(db, app, offering)
    detect_mapping_impact(db, app)


def detect_mapping_impact(db: Session, app: Application) -> None:
    from akus.catalog.service import current_mapping

    allocation = db.get(Allocation, app.id)
    if not allocation or allocation.state == "RELEASED":
        return
    pool = db.get(QuotaPool, allocation.pool_id)
    mapping = current_mapping(db, app.department_id, app.course_id)
    if mapping and pool and mapping.topic_id != pool.topic_id:
        service.case(
            db,
            app,
            "TOPIC_MAPPING",
            "EXISTING_ALLOCATION_POLICY_PENDING_P_NEW_11",
            {
                "current_topic_id": str(pool.topic_id),
                "proposed_topic_id": str(mapping.topic_id),
                "revision_id": str(mapping.id),
            },
        )
