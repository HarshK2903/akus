"""Administrative source authority, independent of academic approval/compliance."""

import json
import re
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.config import Settings
from akus.identity.models import ExternalIdentity, InstitutionalEmail
from akus.identity.service import serialize_links
from akus.models import AcademicYear
from akus.people.models import (
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)
from akus.people.schemas import AppointmentCreate, CommandResult
from akus.people.service import commit_command, detail, lock_command, replay
from akus.sources.models import SourceRevision, Subject, SubjectAlias, TeachingAssignment
from akus.sources.schemas import (
    DepartmentFacts,
    EmailFacts,
    EmploymentFacts,
    PersonFacts,
    ReferenceWrite,
    SourceChange,
    TeachingWrite,
)


def source_context(db: Session, actor: Actor, source: str, reason: str) -> None:
    db.execute(
        text("SELECT set_config('akus.source_context', :context, true)"),
        {
            "context": json.dumps(
                {
                    "actor_person_id": str(actor.person.id),
                    "source_reference": source,
                    "reason": reason,
                }
            )
        },
    )


def revision(db: Session, kind: str, entity_id: UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(SourceRevision)
            .where(SourceRevision.entity_type == kind, SourceRevision.entity_id == entity_id)
        )
        or 1
    )


def check_version(db: Session, kind: str, entity_id: UUID, expected: int | None) -> None:
    if expected != revision(db, kind, entity_id):
        raise HTTPException(409, "SOURCE_CHANGED_REFRESH_REQUIRED")


def validate_teaching(db: Session, body: TeachingWrite) -> EmploymentEpisode:
    episode = db.get(EmploymentEpisode, body.episode_id)
    year = db.get(AcademicYear, body.academic_year_id)
    if not episode or not episode.is_faculty:
        raise HTTPException(422, "TEACHING_REQUIRES_FACULTY_EPISODE")
    if body.starts_on < episode.starts_on or (
        episode.ends_before and body.ends_before > episode.ends_before
    ):
        raise HTTPException(422, "TEACHING_OUTSIDE_EMPLOYMENT")
    if (
        not year
        or body.starts_on < year.starts_on
        or body.ends_before > year.ends_on + timedelta(days=1)
    ):
        raise HTTPException(422, "TEACHING_OUTSIDE_ACADEMIC_YEAR")
    if not db.get(Subject, body.subject_id) or not db.get(Department, body.department_id):
        raise HTTPException(422, "REFERENCE_NOT_FOUND")
    return episode


def write_teaching(
    db: Session, actor: Actor, key: UUID, body: TeachingWrite, record_id: UUID | None = None
) -> CommandResult:
    episode = validate_teaching(db, body)
    actor = lock_command(db, actor, episode.person_id)
    operation = f"TEACHING:{record_id or 'CREATE'}"
    if result := replay(db, actor, key, operation, body):
        return result
    from akus.compliance.assessment import capture

    capture(db, episode)
    validate_teaching(db, body)  # after target person lock, source could have changed
    source_context(db, actor, body.source_reference, body.reason)
    values = body.model_dump(exclude={"reason", "expected_version"})
    if record_id:
        record = db.get(TeachingAssignment, record_id)
        if not record:
            raise HTTPException(404, "NOT_FOUND")
        if record.episode_id != body.episode_id or record.external_key != body.external_key:
            raise HTTPException(409, "TEACHING_IDENTITY_IMMUTABLE")
        if record.version != body.expected_version:
            raise HTTPException(409, "SOURCE_CHANGED_REFRESH_REQUIRED")
        for field, value in values.items():
            setattr(record, field, value)
        record.version += 1
    else:
        record = TeachingAssignment(**values)
        db.add(record)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "TEACHING_INTERVAL_OR_KEY_CONFLICT") from exc
    capture(db, episode)
    return commit_command(
        db,
        actor,
        key,
        operation,
        body,
        record.id,
        {
            "person_id": str(episode.person_id),
            "source_reference": body.source_reference,
            "reason": body.reason,
            "acceptance": "POLICY_PENDING:IO-02",
        },
    )


def scoped_teaching(db: Session, actor: Actor):  # type: ignore[no-untyped-def]
    query = select(TeachingAssignment).join(
        EmploymentEpisode, EmploymentEpisode.id == TeachingAssignment.episode_id
    )
    if set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        return query
    if "HOD" in actor.roles:
        return query.where(TeachingAssignment.department_id.in_(actor.scopes))
    return query.where(EmploymentEpisode.person_id == actor.person.id)


def teaching_view(db: Session, record: TeachingAssignment) -> dict[str, Any]:
    episode = db.get(EmploymentEpisode, record.episode_id)
    assert episode is not None
    person = db.get(Person, episode.person_id)
    subject = db.get(Subject, record.subject_id)
    dept = db.get(Department, record.department_id)
    year = db.get(AcademicYear, record.academic_year_id)
    first = db.scalar(
        select(func.min(TeachingAssignment.starts_on)).where(
            TeachingAssignment.episode_id == record.episode_id,
            TeachingAssignment.subject_id == record.subject_id,
            TeachingAssignment.voided.is_(False),
        )
    )
    deadline = None
    if first:
        try:
            deadline = first.replace(year=first.year + 2)
        except ValueError:
            pass  # P-54, never invent Feb 28 / March 1.
    frozen = None
    if episode.ends_before and episode.ends_before <= datetime.now(ZoneInfo("Asia/Kolkata")).date():
        from akus.exceptions.history import episode_report

        archived = episode_report(db, episode.id, None, datetime.now(ZoneInfo("Asia/Kolkata")))
        frozen = next(
            (s for s in archived["subjects"] if s["subject_id"] == str(record.subject_id)), None
        )
    return {
        "id": record.id,
        "external_key": record.external_key,
        "person_id": episode.person_id,
        "staff_name": person.display_name if person else "Unavailable",
        "episode_id": record.episode_id,
        "subject_id": record.subject_id,
        "subject": subject.name if subject else "Unavailable",
        "department_id": record.department_id,
        "department": dept.name if dept else "Unavailable",
        "academic_year_id": record.academic_year_id,
        "academic_year": year.label if year else "Unavailable",
        "term": record.term,
        "starts_on": record.starts_on,
        "ends_before": record.ends_before,
        "source_reference": record.source_reference,
        "voided": record.voided,
        "version": record.version,
        "recorded_at": record.recorded_at,
        "first_official_date": first,
        "provisional_deadline": deadline,
        "acceptance": "POLICY_PENDING:IO-02",
        "deadline_policy": "POLICY_PENDING:P-54" if first and not deadline else "Q39/Q40/Q42",
        "status_at_separation": frozen["status_at_separation"] if frozen else None,
        "compliance": frozen.get(
            "reassessment",
            frozen["status_at_separation"]
            if frozen.get("archived_obligation_id")
            else "NOT_ASSESSED",
        )
        if frozen
        else "NOT_ASSESSED",
        "episode_closed": bool(
            episode.ends_before
            and episode.ends_before <= datetime.now(ZoneInfo("Asia/Kolkata")).date()
        ),
    }


def write_reference(db: Session, actor: Actor, key: UUID, body: ReferenceWrite) -> CommandResult:
    actor = lock_command(db, actor)
    operation = f"REFERENCE:{body.kind}:{body.id or 'CREATE'}"
    if result := replay(db, actor, key, operation, body):
        return result
    source_context(db, actor, body.source_reference, body.reason)
    record: Department | Subject | SubjectAlias | AcademicYear | None
    if body.kind in {"department", "subject"}:
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,29}", body.code) or len(body.name.strip()) < 2:
            raise HTTPException(422, "CANONICAL_CODE_AND_NAME_REQUIRED")
        model: type[Department] | type[Subject] = (
            Department if body.kind == "department" else Subject
        )
        record = (
            (db.get(Department, body.id) if body.kind == "department" else db.get(Subject, body.id))
            if body.id
            else None
        )
        if body.id and not record:
            raise HTTPException(404, "NOT_FOUND")
        if isinstance(record, (Department, Subject)):
            check_version(db, record.__tablename__, record.id, body.expected_version)
            if body.code != record.code:
                raise HTTPException(409, "CANONICAL_CODE_IMMUTABLE")
            record.name = body.name
            if isinstance(record, Subject):
                record.source_reference, record.version = body.source_reference, record.version + 1
        else:
            record = model(code=body.code, name=body.name)
            if isinstance(record, Subject):
                record.source_reference = body.source_reference
            db.add(record)
    elif body.kind == "alias":
        if not body.subject_id or not db.get(Subject, body.subject_id) or len(body.name) < 2:
            raise HTTPException(422, "SUBJECT_AND_ALIAS_REQUIRED")
        record = db.get(SubjectAlias, body.id) if body.id else None
        if body.id:
            if not record:
                raise HTTPException(404, "NOT_FOUND")
            check_version(db, record.__tablename__, record.id, body.expected_version)
            if record.subject_id != body.subject_id:
                raise HTTPException(423, "SUBJECT_MERGE_POLICY_PENDING")
            record.alias, record.source_reference = body.name.casefold(), body.source_reference
        else:
            record = SubjectAlias(
                subject_id=body.subject_id,
                alias=body.name.casefold(),
                source_reference=body.source_reference,
            )
            db.add(record)
    else:
        if body.id or not body.starts_on or (body.starts_on.month, body.starts_on.day) != (7, 1):
            raise HTTPException(422, "NEW_OFFICIAL_JULY_YEAR_REQUIRED")
        start = body.starts_on
        record = AcademicYear(
            label=f"{start.year}–{str(start.year + 1)[2:]}",
            starts_on=start,
            ends_on=date(start.year + 1, 6, 30),
            source=body.source_reference,
        )
        db.add(record)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "REFERENCE_ALREADY_EXISTS") from exc
    return commit_command(
        db,
        actor,
        key,
        operation,
        body,
        record.id,
        {"source_reference": body.source_reference, "reason": body.reason, "kind": body.kind},
    )


def staff_sources(db: Session, actor: Actor, person_id: UUID) -> dict[str, Any]:
    detail(db, actor, person_id)  # object scope, including own records
    person = db.get(Person, person_id)
    assert person
    episodes = list(
        db.scalars(
            select(EmploymentEpisode)
            .where(EmploymentEpisode.person_id == person_id)
            .order_by(EmploymentEpisode.starts_on)
        )
    )
    memberships = list(
        db.scalars(
            select(DepartmentAssignment)
            .where(DepartmentAssignment.episode_id.in_([e.id for e in episodes]))
            .order_by(DepartmentAssignment.starts_on)
        )
    )
    emails = list(
        db.scalars(
            select(InstitutionalEmail)
            .where(InstitutionalEmail.person_id == person_id)
            .order_by(InstitutionalEmail.valid_from)
        )
    )
    offices = list(
        db.scalars(
            select(OfficeAppointment)
            .where(OfficeAppointment.person_id == person_id)
            .order_by(OfficeAppointment.valid_from)
        )
    )

    def row(record: Any) -> dict[str, Any]:
        return {c.name: getattr(record, c.name) for c in record.__table__.columns} | {
            "source_version": revision(db, record.__tablename__, record.id)
        }

    ids = [
        person_id,
        *[e.id for e in episodes],
        *[m.id for m in memberships],
        *[e.id for e in emails],
        *[o.id for o in offices],
    ]
    history = db.scalars(
        select(SourceRevision)
        .where(SourceRevision.entity_id.in_(ids))
        .order_by(SourceRevision.recorded_at.desc(), SourceRevision.id)
        .limit(100)
    )
    links = (
        list(db.scalars(select(ExternalIdentity).where(ExternalIdentity.person_id == person_id)))
        if "ADMIN" in actor.roles
        else []
    )
    return {
        "person": row(person),
        "episodes": [row(e) for e in episodes],
        "memberships": [row(m) for m in memberships],
        "emails": [row(e) for e in emails],
        "offices": [row(o) for o in offices],
        "identity_links": [
            {"id": link.id, "linked_email": link.linked_email, "revoked_at": link.revoked_at}
            for link in links
        ],
        "history": [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "before": r.before,
                "after": r.after,
                "context": r.context,
                "recorded_at": r.recorded_at,
            }
            for r in history
        ],
    }


def change_source(
    db: Session, actor: Actor, key: UUID, person_id: UUID, body: SourceChange, cfg: Settings
) -> CommandResult:
    if body.kind == "email":
        serialize_links(db)
    actor = lock_command(db, actor, person_id)
    operation = f"SOURCE:{body.kind}:{body.id or person_id}"
    if result := replay(db, actor, key, operation, body):
        return result
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(404, "NOT_FOUND")
    source_context(db, actor, body.source_reference, body.reason)
    try:
        return _change(db, actor, key, person, body, operation, cfg)
    except ValidationError as exc:
        raise HTTPException(422, "INVALID_SOURCE_FIELDS") from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "SOURCE_INTERVAL_OR_KEY_CONFLICT") from exc


def _change(
    db: Session,
    actor: Actor,
    key: UUID,
    person: Person,
    body: SourceChange,
    operation: str,
    cfg: Settings,
) -> CommandResult:
    record: Any
    if body.kind == "person":
        facts = PersonFacts.model_validate(body.values)
        check_version(db, Person.__tablename__, person.id, body.expected_version)
        person.display_name, person.enabled = facts.display_name, facts.enabled
        person.source_reference = body.source_reference
        record = person
    elif body.kind == "employment":
        from akus.compliance.assessment import capture
        from akus.exceptions.models import Departure
        from akus.exceptions.service import process_order

        employment = EmploymentFacts.model_validate(body.values)
        record = db.get(EmploymentEpisode, body.id) if body.id else None
        if body.id:
            if not record or record.person_id != person.id:
                raise HTTPException(404, "NOT_FOUND")
            check_version(db, record.__tablename__, record.id, body.expected_version)
            dependent = list(
                db.scalars(
                    select(TeachingAssignment).where(
                        TeachingAssignment.episode_id == record.id,
                        TeachingAssignment.voided.is_(False),
                    )
                )
            )
            members = list(
                db.scalars(
                    select(DepartmentAssignment).where(DepartmentAssignment.episode_id == record.id)
                )
            )
            bounded: list[TeachingAssignment | DepartmentAssignment] = [*dependent, *members]
            for item in bounded:
                if item.starts_on < employment.starts_on or (
                    employment.ends_before
                    and (not item.ends_before or item.ends_before > employment.ends_before)
                ):
                    raise HTTPException(409, "CORRECT_DEPENDENT_SOURCE_INTERVALS_FIRST")
            if dependent and not employment.is_faculty:
                raise HTTPException(409, "CORRECT_TEACHING_CLASSIFICATION_FIRST")
            offices = list(
                db.scalars(
                    select(OfficeAppointment).where(
                        OfficeAppointment.person_id == person.id,
                        OfficeAppointment.superseded.is_(False),
                        OfficeAppointment.valid_from
                        >= datetime.combine(record.starts_on, time.min, ZoneInfo("Asia/Kolkata")),
                        *(
                            []
                            if not record.ends_before
                            else [
                                OfficeAppointment.valid_from
                                < datetime.combine(
                                    record.ends_before, time.min, ZoneInfo("Asia/Kolkata")
                                )
                            ]
                        ),
                    )
                )
            )
            for office in offices:
                if (
                    office.valid_from.astimezone(ZoneInfo("Asia/Kolkata")).date()
                    < employment.starts_on
                    or (
                        employment.ends_before
                        and (
                            not office.valid_until
                            or office.valid_until
                            > datetime.combine(
                                employment.ends_before, time.min, ZoneInfo("Asia/Kolkata")
                            )
                        )
                    )
                    or (office.office == "DRC_HEAD" and not employment.is_faculty)
                ):
                    raise HTTPException(409, "CORRECT_OFFICE_INTERVALS_FIRST")
            if record.is_faculty:
                capture(db, record)
            for k, v in employment.model_dump().items():
                setattr(record, k, v)
            record.source_reference = body.source_reference
            db.flush()
            order = db.scalar(select(Departure).where(Departure.episode_id == record.id))
            if order:
                process_order(db, order, cfg)
            if record.is_faculty:
                capture(db, record)
        else:
            record = EmploymentEpisode(
                person_id=person.id,
                source_reference=body.source_reference,
                **employment.model_dump(),
            )
            db.add(record)
    elif body.kind == "department":
        membership = DepartmentFacts.model_validate(body.values)
        episode = db.get(EmploymentEpisode, membership.episode_id)
        if (
            not episode
            or episode.person_id != person.id
            or not db.get(Department, membership.department_id)
        ):
            raise HTTPException(422, "EPISODE_OR_DEPARTMENT_NOT_FOUND")
        if membership.starts_on < episode.starts_on or (
            episode.ends_before
            and (not membership.ends_before or membership.ends_before > episode.ends_before)
        ):
            raise HTTPException(422, "MEMBERSHIP_OUTSIDE_EMPLOYMENT")
        record = db.get(DepartmentAssignment, body.id) if body.id else None
        values = membership.model_dump(exclude={"is_faculty"})
        if body.id:
            if not record or record.episode_id != episode.id:
                raise HTTPException(404, "NOT_FOUND")
            check_version(db, record.__tablename__, record.id, body.expected_version)
            for k, v in values.items():
                setattr(record, k, v)
            record.source_reference = body.source_reference
        else:
            record = DepartmentAssignment(**values, source_reference=body.source_reference)
            db.add(record)
    elif body.kind == "email":
        email = EmailFacts.model_validate(body.values)
        domain = email.email.rsplit("@", 1)[1].lower()
        if domain != ("example.test" if cfg.demo_enabled else "cmrit.ac.in"):
            raise HTTPException(422, "EMAIL_ENVIRONMENT_BOUNDARY")
        record = db.get(InstitutionalEmail, body.id) if body.id else None
        if body.id:
            if not record or record.person_id != person.id:
                raise HTTPException(404, "NOT_FOUND")
            check_version(db, record.__tablename__, record.id, body.expected_version)
            for k, v in email.model_dump().items():
                setattr(record, k, v)
            record.normalized_email, record.source_reference = (
                email.email.lower(),
                body.source_reference,
            )
        else:
            record = InstitutionalEmail(
                person_id=person.id,
                normalized_email=email.email.lower(),
                source_reference=body.source_reference,
                **email.model_dump(),
            )
            db.add(record)
    else:
        # Replacing a mistaken appointment preserves issued facts and removes its projection
        # from exclusion constraints atomically. All new authority is validated again.
        record = db.get(OfficeAppointment, body.id) if body.id else None
        if not record or record.person_id != person.id or record.superseded:
            raise HTTPException(404, "NOT_FOUND")
        if body.expected_version != record.version:
            raise HTTPException(409, "SOURCE_CHANGED_REFRESH_REQUIRED")
        appointment = AppointmentCreate.model_validate(
            body.values
            | {
                "person_id": person.id,
                "source_reference": body.source_reference,
                "reason": body.reason,
            }
        )
        record.superseded, record.version = True, record.version + 1
        db.flush()
        # create_appointment rechecks live authority, employment and global exclusions.
        # Receipt uses a distinct deterministic key; outer source receipt is appended in
        # the same transaction via an internal non-committing helper (below).
        return replace_office(db, actor, key, body, appointment, record, operation)
    db.flush()
    return commit_command(
        db,
        actor,
        key,
        operation,
        body,
        record.id,
        {
            "person_id": str(person.id),
            "reason": body.reason,
            "source_reference": body.source_reference,
        },
    )


def replace_office(
    db: Session,
    actor: Actor,
    key: UUID,
    body: SourceChange,
    values: AppointmentCreate,
    old: OfficeAppointment,
    operation: str,
) -> CommandResult:
    from akus.people.service import validate_office

    validate_office(db, values)
    replacement = OfficeAppointment(**values.model_dump(), original_until=values.valid_until)
    db.add(replacement)
    db.flush()
    return commit_command(
        db,
        actor,
        key,
        operation,
        body,
        replacement.id,
        {
            "person_id": str(old.person_id),
            "supersedes": str(old.id),
            "reason": body.reason,
            "source_reference": body.source_reference,
        },
    )
