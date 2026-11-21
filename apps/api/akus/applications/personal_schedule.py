"""Manual HoD verification authority confirmed by the user on 2026-11-18.

No enrollment, participation or certificate is verified by this date-only finding.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import service
from akus.applications.models import PersonalSchedule, PersonalScheduleCurrent
from akus.applications.schemas import VerifySchedule
from akus.catalog import common
from akus.people.schemas import CommandResult


def current(db: Session, app_id: UUID) -> PersonalSchedule | None:
    return db.scalar(
        select(PersonalSchedule)
        .join(PersonalScheduleCurrent, PersonalScheduleCurrent.revision_id == PersonalSchedule.id)
        .where(PersonalScheduleCurrent.application_id == app_id)
    )


def verify(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: VerifySchedule
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, offering = service.lock_application(db, app_id, actor)
    office = common.require_hod(actor, app.department_id)
    if app.person_id == actor.person.id:
        raise HTTPException(403, "SELF_VERIFICATION_PROHIBITED")
    op = f"PERSON_SCHEDULE_VERIFIED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    if app.state not in {"UNDER_REVIEW", "APPROVED"} or not service.applicant_still_eligible(
        db, app
    ):
        raise HTTPException(423, "LIVE_ELIGIBLE_APPLICATION_REQUIRED")
    prior = current(db, app_id)
    if body.expected_version != (prior.version if prior else 0):
        raise HTTPException(409, "VERSION_CONFLICT")
    if prior and body.observed_at < prior.observed_at:
        raise HTTPException(409, "STALE_PERSON_SCHEDULE_EVIDENCE")
    common.require_person_evidence(db, body.source_reference, body.document_digest)
    revision = PersonalSchedule(
        id=uuid4(),
        application_id=app.id,
        version=body.expected_version + 1,
        scheduled_exam_on=body.scheduled_exam_on,
        source_reference=body.source_reference,
        document_digest=body.document_digest,
        observed_at=body.observed_at,
        actor_id=actor.person.id,
        office_id=office.id,
        reason=body.reason,
    )
    db.add(revision)
    db.flush()
    pointer = db.get(PersonalScheduleCurrent, app.id)
    if pointer:
        pointer.revision_id = revision.id
    else:
        db.add(PersonalScheduleCurrent(application_id=app.id, revision_id=revision.id))
    db.flush()
    service.resolve_case(db, app, "PERSON_SCHEDULE", "HOD_AUTHENTICATED_OFFICIAL_EVIDENCE")
    from akus.applications.transfers import reconcile

    reconcile(db, app, offering, actor)
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        body.model_dump(mode="json")
        | {
            "revision_id": str(revision.id),
            "office_id": str(office.id),
            "person_id": str(app.person_id),
            "offering_id": str(offering.id),
            "verification": "MANUAL_HOD_AUTHENTICATED",
            "policy": "USER_CONFIRMED_2026-11-18",
        },
        app.department_id,
    )
