from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications.models import Allocation, Application, Reconciliation
from akus.compliance import assessment
from akus.exceptions.models import Departure
from akus.exceptions.schemas import IST
from akus.people.models import (
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
)
from akus.people.schemas import CommandResult
from akus.people.service import commit_command, lock_command, replay
from akus.sources.schemas import Rehire
from akus.sources.service import check_version, source_context


def rehire(db: Session, actor: Actor, key: UUID, person_id: UUID, body: Rehire) -> CommandResult:
    actor = lock_command(db, actor, person_id)
    op = f"REHIRE:{person_id}"
    if result := replay(db, actor, key, op, body):
        return result
    previous = db.scalar(
        select(EmploymentEpisode)
        .where(EmploymentEpisode.person_id == person_id)
        .order_by(EmploymentEpisode.starts_on.desc())
        .limit(1)
    )
    if not previous or previous.id != body.previous_episode_id:
        raise HTTPException(409, "LATEST_EPISODE_REQUIRED")
    check_version(db, previous.__tablename__, previous.id, body.expected_version)
    if not previous.ends_before or body.starts_on < previous.ends_before:
        raise HTTPException(409, "REHIRE_OVERLAPS_PREVIOUS_EMPLOYMENT")
    order = db.scalar(select(Departure).where(Departure.episode_id == previous.id))
    if order and order.effective_on != previous.ends_before:
        raise HTTPException(409, "PERMANENT_ORDER_SOURCE_CONFLICT")
    if not db.get(Department, body.department_id):
        raise HTTPException(422, "REFERENCE_NOT_FOUND")
    source_context(db, actor, body.source_reference, body.reason)
    episode = EmploymentEpisode(
        person_id=person_id,
        starts_on=body.starts_on,
        is_faculty=body.is_faculty,
        source_reference=body.source_reference,
    )
    try:
        db.add(episode)
        db.flush()
        membership = DepartmentAssignment(
            episode_id=episode.id,
            starts_on=body.starts_on,
            department_id=body.department_id,
            source_reference=body.source_reference,
        )
        db.add(membership)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "SOURCE_INTERVAL_OR_KEY_CONFLICT") from exc
    return commit_command(
        db,
        actor,
        key,
        op,
        body,
        episode.id,
        {
            "person_id": str(person_id),
            "previous_episode_id": str(previous.id),
            "membership_id": str(membership.id),
            "department_id": str(body.department_id),
            "starts_on": body.starts_on.isoformat(),
            "source_reference": body.source_reference,
            "reason": body.reason,
        },
    )


def impact(
    db: Session, ep: EmploymentEpisode, effective_on: date, offset: int, limit: int
) -> dict[str, Any]:
    if effective_on <= ep.starts_on:
        raise HTTPException(422, "END_MUST_FOLLOW_EMPLOYMENT_START")
    order = db.scalar(select(Departure).where(Departure.episode_id == ep.id))
    apps = select(Application).where(Application.episode_id == ep.id)
    total = db.scalar(select(func.count()).select_from(apps.subquery()))
    rows = db.execute(
        apps.outerjoin(Allocation, Allocation.application_id == Application.id)
        .add_columns(Allocation.state, Allocation.pool_id)
        .order_by(Application.created_at, Application.id)
        .offset(offset)
        .limit(limit)
    )
    applications = []
    for app, state, pool in rows:
        cases = list(
            db.scalars(
                select(Reconciliation.reason)
                .where(Reconciliation.application_id == app.id, Reconciliation.status == "OPEN")
                .order_by(Reconciliation.kind)
            )
        )
        applications.append(
            {
                "id": app.id,
                "state": app.state,
                "pool_id": pool,
                "allocation": state,
                "open_reviews": cases,
            }
        )
    subjects = assessment.subject_rows(db, ep, [], effective_on)
    boundary = datetime.combine(effective_on, time.min, IST)
    offices = select(OfficeAppointment).where(
        OfficeAppointment.person_id == ep.person_id,
        OfficeAppointment.superseded.is_(False),
        OfficeAppointment.valid_from >= datetime.combine(ep.starts_on, time.min, IST),
        or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > boundary),
    )
    if ep.ends_before:
        offices = offices.where(
            OfficeAppointment.valid_from < datetime.combine(ep.ends_before, time.min, IST)
        )
    return {
        "effective_on": effective_on,
        "recorded_at": ep.recorded_at,
        "order": {
            "effective_on": order.effective_on,
            "effective_at": order.effective_at,
            "recorded_at": order.recorded_at,
            "source_reference": order.proof["source_reference"],
        }
        if order
        else None,
        "applications": applications,
        "total": total,
        "subjects": [
            {
                "subject": s["subject"],
                "first_assignment": s["first_assignment"],
                "deadline": s["deadline"],
            }
            for s in subjects
        ],
        "offices": [
            {"office": o.office, "valid_from": o.valid_from, "valid_until": o.valid_until}
            for o in db.scalars(offices.order_by(OfficeAppointment.valid_from))
        ],
    }
