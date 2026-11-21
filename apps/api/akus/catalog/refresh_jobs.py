"""Durable public-metadata observations. Network I/O runs between transactions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.catalog import common, provider, service
from akus.catalog.models import AcademicEvent, Offering
from akus.catalog.schemas import OfferingFetch
from akus.models import AuditEvent, WorkJob
from akus.people.schemas import CommandResult
from akus.people.service import require_admin

KIND = "PROVIDER_REFRESH"
QUEUED = "PROVIDER_REFRESH_QUEUED"


def enqueue(db: Session, actor: Actor, key: UUID, body: OfferingFetch) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    if receipt := common.replay(db, actor, key, QUEUED, body):
        return receipt
    service.get_course(db, body.course_id)
    other = db.scalar(select(Offering.course_id).where(Offering.provider_id == body.provider_id))
    if other and other != body.course_id:
        raise HTTPException(409, "OFFERING_CANONICAL_IDENTITY_CONFLICT")
    job = WorkJob(id=uuid4(), kind=KIND, key="provider:" + str(uuid4()))
    db.add(job)
    return common.finish(
        db,
        actor,
        key,
        QUEUED,
        body,
        job.id,
        {"request": body.model_dump(mode="json"), "episode": str(actor.episode.id)},
    )


def authorized(db: Session, source: AcademicEvent) -> bool:
    # The issuing employment episode and Admin grant must still be effective.
    # Workers have no browser identity, provider token or authority to accept a snapshot.
    db.execute(text("SELECT pg_advisory_xact_lock_shared(8210402)"))
    return bool(
        db.scalar(
            text("""SELECT EXISTS(SELECT 1 FROM persons p JOIN employment_episodes e ON e.person_id=p.id
    JOIN faculty_department_appointments a ON a.episode_id=e.id JOIN administrative_grants g ON g.person_id=p.id
    WHERE p.id=:issuer AND p.enabled AND e.id=:episode
    AND daterange(e.starts_on,e.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
    AND daterange(a.starts_on,a.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
    AND g.valid_from<=now() AND (g.valid_until IS NULL OR g.valid_until>now())
    AND NOT EXISTS(SELECT 1 FROM permanent_departures d WHERE d.episode_id=e.id
    AND d.effective_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date AND (d.effective_at IS NULL OR d.effective_at<=now())))"""),
            {"issuer": source.actor_id, "episode": UUID(source.data["episode"])},
        )
    )


def outcome(db: Session, job: WorkJob, error: str | None, *, terminal: bool = False) -> None:
    job.last_error = error
    job.next_attempt_at = None
    if error and not terminal and job.attempts % 3:
        job.next_attempt_at = datetime.now(UTC) + timedelta(seconds=15 * job.attempts)
    else:
        job.state = "DEAD" if error else "DONE"
    db.add(
        AuditEvent(
            action="PROVIDER_REFRESH_RESULT",
            details={
                "job_id": str(job.id),
                "attempt": str(job.attempts),
                "state": job.state,
                "outcome": error or "OBSERVED",
            },
        )
    )


def run_one(factory: sessionmaker[Session], job_id: UUID | None = None) -> bool:
    with factory.begin() as db:
        now = datetime.now(UTC)
        q = select(WorkJob).where(
            WorkJob.kind == KIND,
            WorkJob.state == "PENDING",
            or_(WorkJob.next_attempt_at.is_(None), WorkJob.next_attempt_at <= now),
        )
        if job_id:
            q = q.where(WorkJob.id == job_id)
        job = db.scalar(q.order_by(WorkJob.created_at).with_for_update(skip_locked=True).limit(1))
        if not job:
            return False
        source = db.scalar(
            select(AcademicEvent).where(
                AcademicEvent.entity_id == job.id, AcademicEvent.kind == QUEUED
            )
        )
        if not source or not source.actor_id or not authorized(db, source):
            outcome(db, job, "SOURCE_AUTHORITY_EXPIRED", terminal=True)
            return True
        if job.next_attempt_at and job.attempts and job.attempts % 3 == 0:
            outcome(db, job, "FETCH_LEASE_EXPIRED", terminal=True)
            return True
        issuer, source_id = source.actor_id, source.id
        body = OfferingFetch.model_validate(source.data["request"])
        job.attempts += 1
        attempt, jid = job.attempts, job.id
        job.next_attempt_at = now + timedelta(minutes=2)
    observation, error = None, None
    try:
        observation = provider.fetch(body.provider_id)
    except provider.ProviderError as exc:
        error = str(exc)
    with factory.begin() as db:
        # Source authority precedes resource locks, as in synchronous source commands.
        source = db.get_one(AcademicEvent, source_id)
        can_record = authorized(db, source)
        locked = db.scalar(select(WorkJob).where(WorkJob.id == jid).with_for_update())
        assert locked is not None
        if locked.attempts != attempt or locked.state != "PENDING":
            return True
        if not can_record:
            outcome(db, locked, "SOURCE_AUTHORITY_EXPIRED", terminal=True)
            return True
        try:
            with db.begin_nested():
                service.persist_observation(db, issuer, body, observation, error)
        except HTTPException as exc:
            outcome(db, locked, str(exc.detail), terminal=True)
        else:
            outcome(db, locked, error)
    return True
