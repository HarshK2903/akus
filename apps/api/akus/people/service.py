"""Commands own transactions; query scope is always resolved on the server."""

from datetime import UTC, datetime, time
from hashlib import sha256
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor, authority
from akus.identity.models import ExternalIdentity, InstitutionalSession
from akus.models import AuditEvent, AuthSession
from akus.people.models import (
    CommandReceipt,
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)
from akus.people.schemas import (
    AppointmentCreate,
    AppointmentEnd,
    AppointmentPage,
    AppointmentView,
    CommandResult,
    EpisodeView,
    HistoryEvent,
    StaffCreate,
    StaffDetail,
    StaffPage,
    StaffSummary,
)


def require_admin(actor: Actor) -> None:
    if "ADMIN" not in actor.roles:
        raise HTTPException(403, "ADMIN_AUTHORITY_REQUIRED")


def require_directory(actor: Actor) -> None:
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL", "HOD"}:
        raise HTTPException(403, "DIRECTORY_ACCESS_DENIED")


def lock_command(db: Session, actor: Actor, target: UUID | None = None) -> Actor:
    require_admin(actor)
    # One short source-command lock precedes person locks across imports, corrections
    # and identity reconciliation. No provider HTTP is performed in this transaction.
    db.execute(text("SELECT pg_advisory_xact_lock(8210402)"))
    person_id, token_hash = actor.person.id, actor.session.token_hash
    institutional = isinstance(actor.session, InstitutionalSession)
    db.expire_all()
    live_session = (
        db.get(InstitutionalSession, token_hash)
        if institutional
        else db.get(AuthSession, token_hash)
    )
    if live_session is None or live_session.expires_at <= datetime.now(UTC):
        raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    if isinstance(live_session, InstitutionalSession):
        link = db.get(ExternalIdentity, live_session.external_identity_id)
        if not link or link.revoked_at or link.person_id != person_id:
            raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    ids = {person_id, target} - {None}
    list(
        db.scalars(
            select(Person)
            .where(Person.id.in_(ids))
            .order_by(Person.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )
    fresh = authority(db, actor.demo, live_session)
    require_admin(fresh)
    return fresh


def request_digest(body: BaseModel) -> str:
    return sha256(body.model_dump_json().encode()).hexdigest()


def replay(
    db: Session, actor: Actor, key: UUID, operation: str, body: BaseModel
) -> CommandResult | None:
    previous = db.scalar(
        select(CommandReceipt).where(
            CommandReceipt.actor_id == actor.person.id, CommandReceipt.key == key
        )
    )
    if previous is None:
        return None
    if previous.operation != operation or previous.request_hash != request_digest(body):
        raise HTTPException(409, "IDEMPOTENCY_KEY_REUSED")
    return CommandResult(id=UUID(previous.result["id"]))


def commit_command(
    db: Session,
    actor: Actor,
    key: UUID,
    operation: str,
    body: BaseModel,
    entity_id: UUID,
    details: dict[str, str],
) -> CommandResult:
    db.add(
        CommandReceipt(
            actor_id=actor.person.id,
            key=key,
            operation=operation,
            request_hash=request_digest(body),
            result={"id": str(entity_id)},
        )
    )
    db.add(
        AuditEvent(
            actor_id=actor.demo.id if actor.demo else None,
            action="OFFICE_ENDED" if operation.startswith("END:") else operation,
            details=details
            | {
                "actor_person_id": str(actor.person.id),
                "entity_id": str(entity_id),
                "authority": "ADMIN",
                "policy": "A02/I02; source administration",
            },
        )
    )
    try:
        from akus.applications.models import Application
        from akus.models import WorkJob

        # Source facts may change eligibility of already counted applications.
        # Reconcile after commit, with current facts; never guess separation policy.
        for app_id in db.scalars(
            select(Application.id).where(
                Application.state.in_(["UNDER_REVIEW", "APPROVED", "WITHDRAWN"]),
                Application.person_id
                == (UUID(details["person_id"]) if details.get("person_id") else None),
            )
        ):
            db.add(
                WorkJob(key=f"recheck:{app_id}:{uuid4()}", kind="QUOTA_RECHECK", state="PENDING")
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "SOURCE_RECORD_CONFLICT") from exc
    return CommandResult(id=entity_id)


def create_staff(db: Session, actor: Actor, key: UUID, body: StaffCreate) -> CommandResult:
    actor = lock_command(db, actor)
    if result := replay(db, actor, key, "STAFF_CREATED", body):
        return result
    if db.get(Department, body.department_id) is None:
        raise HTTPException(422, "DEPARTMENT_NOT_FOUND")
    if db.scalar(select(Person.id).where(Person.staff_key == body.staff_key)):
        raise HTTPException(409, "STAFF_KEY_EXISTS")
    person = Person(
        staff_key=body.staff_key,
        display_name=body.display_name,
        enabled=True,
        source_reference=body.source_reference,
    )
    db.add(person)
    try:
        db.flush()
        episode = EmploymentEpisode(
            person_id=person.id,
            starts_on=body.starts_on,
            ends_before=None,
            is_faculty=body.is_faculty,
            source_reference=body.source_reference,
        )
        db.add(episode)
        db.flush()
        db.add(
            DepartmentAssignment(
                episode_id=episode.id,
                department_id=body.department_id,
                starts_on=body.starts_on,
                ends_before=None,
                source_reference=body.source_reference,
            )
        )
        return commit_command(
            db,
            actor,
            key,
            "STAFF_CREATED",
            body,
            person.id,
            {
                "person_id": str(person.id),
                "source_reference": body.source_reference,
                "reason": body.reason,
                "starts_on": str(body.starts_on),
            },
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "STAFF_KEY_EXISTS") from exc


def validate_office(db: Session, body: AppointmentCreate) -> None:
    person = db.get(Person, body.person_id)
    if person is None or not person.enabled:
        raise HTTPException(422, "STAFF_NOT_PROVISIONED")
    local_start = body.valid_from.astimezone(ZoneInfo("Asia/Kolkata")).date()
    episode = db.scalar(
        select(EmploymentEpisode).where(
            EmploymentEpisode.person_id == person.id,
            EmploymentEpisode.starts_on <= local_start,
            or_(
                EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > local_start
            ),
        )
    )
    if episode is None:
        raise HTTPException(422, "OFFICE_OUTSIDE_EMPLOYMENT")
    if episode.ends_before is not None:
        if body.valid_until is None or body.valid_until > datetime.combine(
            episode.ends_before, time.min, tzinfo=ZoneInfo("Asia/Kolkata")
        ):
            raise HTTPException(422, "OFFICE_OUTSIDE_EMPLOYMENT")
    if body.office == "DRC_HEAD" and not episode.is_faculty:
        raise HTTPException(422, "DRC_REQUIRES_FACULTY")
    if body.department_id is not None and db.get(Department, body.department_id) is None:
        raise HTTPException(422, "DEPARTMENT_NOT_FOUND")
    # Separate conflict with Principal has no ratified resolution: fail closed.
    conflict = db.scalar(
        select(OfficeAppointment.id).where(
            OfficeAppointment.person_id == body.person_id,
            OfficeAppointment.superseded.is_(False),
            OfficeAppointment.office.in_(
                ["HOD", "ACTING_HOD", "DRC_HEAD"] if body.office == "PRINCIPAL" else ["PRINCIPAL"]
            ),
            func.tstzrange(OfficeAppointment.valid_from, OfficeAppointment.valid_until, "[)").op(
                "&&"
            )(func.tstzrange(body.valid_from, body.valid_until, "[)")),
        )
    )
    if conflict:
        raise HTTPException(423, "AUTHORITY_POLICY_PENDING")


def create_appointment(
    db: Session, actor: Actor, key: UUID, body: AppointmentCreate
) -> CommandResult:
    actor = lock_command(db, actor, body.person_id)
    if result := replay(db, actor, key, "OFFICE_APPOINTED", body):
        return result
    validate_office(db, body)
    record = OfficeAppointment(**body.model_dump(), original_until=body.valid_until)
    db.add(record)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "OFFICE_INTERVAL_CONFLICT") from exc
    return commit_command(
        db,
        actor,
        key,
        "OFFICE_APPOINTED",
        body,
        record.id,
        {
            "person_id": str(body.person_id),
            "office": body.office,
            "department_id": str(body.department_id or "INSTITUTION"),
            "valid_from": body.valid_from.isoformat(),
            "original_until": body.valid_until.isoformat() if body.valid_until else "OPEN",
            "source_reference": body.source_reference,
            "reason": body.reason,
        },
    )


def end_appointment(
    db: Session, actor: Actor, key: UUID, appointment_id: UUID, body: AppointmentEnd
) -> CommandResult:
    require_admin(actor)
    record = db.get(OfficeAppointment, appointment_id)
    if record is None:
        raise HTTPException(404, "NOT_FOUND")
    actor = lock_command(db, actor, record.person_id)
    operation = f"END:{appointment_id}"
    if result := replay(db, actor, key, operation, body):
        return result
    db.refresh(record, with_for_update=True)
    now = datetime.now(UTC)
    if record.version != body.expected_version:
        raise HTTPException(409, "OPTIMISTIC_LOCK_CONFLICT")
    if (
        record.superseded
        or record.valid_from >= now
        or (record.valid_until and record.valid_until <= now)
    ):
        raise HTTPException(409, "OFFICE_NOT_CURRENT")
    previous_until = record.valid_until
    record.valid_until = now
    record.version += 1
    # action is a fixed audit kind; receipt operation remains entity-specific.
    result = commit_command(
        db,
        actor,
        key,
        operation,
        body,
        record.id,
        {
            "person_id": str(record.person_id),
            "office": record.office,
            "previous_until": previous_until.isoformat() if previous_until else "OPEN",
            "ended_at": now.isoformat(),
            "reason": body.reason,
        },
    )
    return result


def staff_scope(actor: Actor, now: datetime):  # type: ignore[no-untyped-def]
    query = select(Person)
    if set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        return query
    if "HOD" in actor.roles:
        today = now.astimezone(ZoneInfo("Asia/Kolkata")).date()
        return query.where(
            Person.id.in_(
                select(EmploymentEpisode.person_id)
                .join(DepartmentAssignment, DepartmentAssignment.episode_id == EmploymentEpisode.id)
                .where(
                    DepartmentAssignment.department_id.in_(actor.scopes),
                    EmploymentEpisode.starts_on <= today,
                    or_(
                        EmploymentEpisode.ends_before.is_(None),
                        EmploymentEpisode.ends_before > today,
                    ),
                    DepartmentAssignment.starts_on <= today,
                    or_(
                        DepartmentAssignment.ends_before.is_(None),
                        DepartmentAssignment.ends_before > today,
                    ),
                )
            )
        )
    return query.where(Person.id == actor.person.id)


def staff_summary(db: Session, person: Person, now: datetime) -> StaffSummary:
    today = now.astimezone(ZoneInfo("Asia/Kolkata")).date()
    episode = db.scalar(
        select(EmploymentEpisode).where(
            EmploymentEpisode.person_id == person.id,
            EmploymentEpisode.starts_on <= today,
            or_(EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > today),
        )
    )
    assignment = (
        db.scalar(
            select(DepartmentAssignment).where(
                DepartmentAssignment.episode_id == episode.id,
                DepartmentAssignment.starts_on <= today,
                or_(
                    DepartmentAssignment.ends_before.is_(None),
                    DepartmentAssignment.ends_before > today,
                ),
            )
        )
        if episode
        else None
    )
    department = db.get(Department, assignment.department_id) if assignment else None
    offices = (
        list(
            db.scalars(
                select(OfficeAppointment.office).where(
                    OfficeAppointment.person_id == person.id,
                    OfficeAppointment.superseded.is_(False),
                    OfficeAppointment.valid_from <= now,
                    or_(
                        OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now
                    ),
                )
            )
        )
        if episode and person.enabled
        else []
    )
    return StaffSummary(
        id=person.id,
        staff_key=person.staff_key,
        display_name=person.display_name,
        department=department.name if department else None,
        department_id=department.id if department else None,
        employment_status="ACTIVE" if episode and person.enabled else "INACTIVE",
        offices=offices,
    )


def list_staff(db: Session, actor: Actor, q: str, offset: int, limit: int) -> StaffPage:
    require_directory(actor)
    now = datetime.now(UTC)
    query = staff_scope(actor, now)
    if q:
        query = query.where(
            or_(
                Person.display_name.icontains(q, autoescape=True),
                Person.staff_key.icontains(q, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    people = db.scalars(query.order_by(Person.display_name, Person.id).offset(offset).limit(limit))
    return StaffPage(
        items=[staff_summary(db, p, now) for p in people], total=total, offset=offset, limit=limit
    )


def appointment_view(db: Session, record: OfficeAppointment, now: datetime) -> AppointmentView:
    person = db.get(Person, record.person_id)
    department = db.get(Department, record.department_id) if record.department_id else None
    status = (
        "SUPERSEDED"
        if record.superseded
        else "ENDED"
        if record.valid_until and record.valid_until <= now
        else "SCHEDULED"
        if record.valid_from > now
        else "CURRENT"
    )
    return AppointmentView(
        id=record.id,
        person_id=record.person_id,
        person_name=person.display_name if person else "Unavailable",
        office=record.office,
        department_id=record.department_id,
        department=department.name if department else None,
        valid_from=record.valid_from,
        valid_until=record.valid_until,
        original_until=record.original_until,
        source_reference=record.source_reference,
        reason=record.reason,
        recorded_at=record.recorded_at,
        version=record.version,
        status=status,
    )


def detail(db: Session, actor: Actor, person_id: UUID) -> StaffDetail:
    now = datetime.now(UTC)
    person = (
        db.get(Person, person_id)
        if person_id == actor.person.id
        else db.scalar(staff_scope(actor, now).where(Person.id == person_id))
    )
    if person is None:
        raise HTTPException(404, "NOT_FOUND")
    episodes = list(
        db.scalars(
            select(EmploymentEpisode)
            .where(EmploymentEpisode.person_id == person_id)
            .order_by(EmploymentEpisode.starts_on)
        )
    )
    appointments = list(
        db.scalars(
            select(OfficeAppointment)
            .where(OfficeAppointment.person_id == person_id)
            .order_by(OfficeAppointment.valid_from.desc())
        )
    )
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.details["person_id"].astext == str(person_id))
        .order_by(AuditEvent.recorded_at.desc(), AuditEvent.id)
        .limit(100)
    )
    return StaffDetail(
        person=staff_summary(db, person, now),
        source_reference=person.source_reference,
        recorded_at=person.recorded_at,
        episodes=[EpisodeView.model_validate(e) for e in episodes],
        appointments=[appointment_view(db, a, now) for a in appointments],
        events=[
            HistoryEvent(id=e.id, action=e.action, recorded_at=e.recorded_at, details=e.details)
            for e in events
        ],
    )


def list_appointments(db: Session, actor: Actor, offset: int, limit: int) -> AppointmentPage:
    require_directory(actor)
    now = datetime.now(UTC)
    query = select(OfficeAppointment)
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        query = query.where(OfficeAppointment.department_id.in_(actor.scopes))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    records = db.scalars(
        query.order_by(OfficeAppointment.valid_from.desc(), OfficeAppointment.id)
        .offset(offset)
        .limit(limit)
    )
    return AppointmentPage(
        items=[appointment_view(db, a, now) for a in records],
        total=total,
        offset=offset,
        limit=limit,
    )


def appointment_detail(db: Session, actor: Actor, appointment_id: UUID) -> AppointmentView:
    record = db.get(OfficeAppointment, appointment_id)
    if record is None:
        raise HTTPException(404, "NOT_FOUND")
    if not (
        set(actor.roles) & {"ADMIN", "PRINCIPAL"}
        or record.person_id == actor.person.id
        or ("HOD" in actor.roles and record.department_id in actor.scopes)
    ):
        raise HTTPException(404, "NOT_FOUND")
    return appointment_view(db, record, datetime.now(UTC))
