"""Office continuity and external dates for pending institutional reviews."""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import service as apps
from akus.applications.models import AcademicNotice, Application, Reconciliation, Submission
from akus.catalog.models import Offering
from akus.catalog.service import snapshot
from akus.exceptions.schemas import IST
from akus.exceptions.service import exclusive
from akus.people.models import (
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)


def waiting() -> Select[tuple[Application]]:
    cases = select(Reconciliation.application_id).where(
        Reconciliation.kind == "SEPARATION", Reconciliation.status == "OPEN"
    )
    return (
        select(Application)
        .where(or_(Application.state == "UNDER_REVIEW", Application.id.in_(cases)))
        .order_by(Application.submitted_at, Application.id)
    )


def sources(db: Session, app: Application) -> dict[str, Any]:
    now = datetime.now(UTC)
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.kind == "SEPARATION",
            Reconciliation.status == "OPEN",
            Reconciliation.application_id == app.id,
        )
    )
    required = (
        "HOD"
        if case
        and case.reason
        in {"Q44_HOD_REVIEW", "ENROLLMENT_CHRONOLOGY_REQUIRED", "Q47_CHRONOLOGY_REVIEW"}
        else None
        if case
        else app.next_office
    )
    day = now.astimezone(IST).date()
    office = db.scalar(
        select(OfficeAppointment)
        .join(Person)
        .join(EmploymentEpisode, EmploymentEpisode.person_id == Person.id)
        .join(DepartmentAssignment, DepartmentAssignment.episode_id == EmploymentEpisode.id)
        .where(
            OfficeAppointment.department_id == app.department_id,
            OfficeAppointment.office_group == required,
            OfficeAppointment.valid_from <= now,
            or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now),
            OfficeAppointment.superseded.is_(False),
            Person.enabled.is_(True),
            Person.id != app.person_id,
            EmploymentEpisode.starts_on <= day,
            or_(EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > day),
            DepartmentAssignment.starts_on <= day,
            or_(DepartmentAssignment.ends_before.is_(None), DepartmentAssignment.ends_before > day),
        )
    )
    offering = db.get(Offering, app.offering_id)
    assert offering
    source = snapshot(db, offering)
    sub = db.get(Submission, app.id)
    published = source.metadata_json if source else {}
    reviewer = db.get(Person, office.person_id) if office else None
    cutoff = min(
        (
            day
            for day in (
                sub.facts["metadata"].get("enrollment_ends_on") if sub else None,
                published.get("enrollment_ends_on"),
            )
            if day
        ),
        default=None,
    )
    days = (date.fromisoformat(cutoff) - apps.today()).days if cutoff else None
    return {
        "deadline_status": "UNKNOWN"
        if days is None
        else "PASSED"
        if days < 0
        else "DUE_TODAY"
        if days == 0
        else "UPCOMING",
        "office": required or "EVIDENCE_REVIEW",
        "task": "SEPARATION" if case else "APPLICATION_REVIEW",
        "appointment_id": str(office.id) if office else None,
        "reviewer": reviewer.display_name if reviewer else None,
        "status": "ASSIGNED" if office else "VACANT" if required else "EVIDENCE_OR_POLICY_PENDING",
        "offering": offering.provider_id,
        "original_enrollment_cutoff": sub.facts["metadata"]["enrollment_ends_on"] if sub else None,
        "enrollment_cutoff": published.get("enrollment_ends_on"),
        "exam_registration_cutoff": published.get("exam_registration_ends_on"),
    }


def pending(db: Session, actor: Actor, offset: int, vacant_only: bool) -> dict[str, Any]:
    query = waiting()
    if not ({"PRINCIPAL", "ADMIN"} & set(actor.roles)):
        departments = [o.department_id for o in actor.offices if o.office in {"HOD", "ACTING_HOD"}]
        if not departments:
            raise HTTPException(403, "OFFICE_OVERSIGHT_REQUIRED")
        query = query.where(Application.department_id.in_(departments))
    rows = []
    for app in db.scalars(query):
        row = sources(db, app)
        if vacant_only and row["status"] != "VACANT":
            continue
        department = db.get(Department, app.department_id)
        rows.append(
            row
            | {"application_id": str(app.id), "department": department.name if department else None}
        )
    return {"items": rows[offset : offset + 25], "total": len(rows), "today": apps.today()}


def notify_changes(db: Session) -> None:
    exclusive(db)
    for app in db.scalars(waiting()):
        facts = sources(db, app)
        prev = db.scalar(
            select(AcademicNotice)
            .where(
                AcademicNotice.application_id == app.id,
                AcademicNotice.kind == "REVIEW_OFFICE_ALERT",
            )
            .order_by(AcademicNotice.created_at.desc(), AcademicNotice.id)
            .limit(1)
        )
        if (
            prev is None
            and facts["status"] != "VACANT"
            and facts["deadline_status"] not in {"DUE_TODAY", "PASSED"}
        ):
            continue
        if not prev or prev.facts != facts:
            apps.notice(db, app, "REVIEW_OFFICE_ALERT", facts)
