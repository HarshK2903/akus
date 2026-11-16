"""Current authority from source records. Demo role labels never grant access."""

from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.auth import digest, resolve
from akus.identity.models import ExternalIdentity, InstitutionalSession
from akus.models import AuthSession, DemoIdentity
from akus.people.models import (
    AdministrativeGrant,
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)
from akus.schemas import Identity

COOKIE = "akus_demo_session"


def get_db(request: Request) -> Generator[Session]:
    with request.app.state.sessions() as session:
        yield session


DB = Annotated[Session, Depends(get_db)]


@dataclass
class Actor:
    session: AuthSession | InstitutionalSession
    demo: DemoIdentity | None
    person: Person
    episode: EmploymentEpisode
    department: Department
    offices: list[OfficeAppointment]
    roles: list[str]
    scopes: list[UUID]

    @property
    def primary_role(self) -> str:
        return next(
            (r for r in ["ADMIN", "PRINCIPAL", "HOD", "DRC_HEAD", "FACULTY"] if r in self.roles),
            "STAFF",
        )

    def view(self) -> Identity:
        exempt = any(r in self.roles for r in ["PRINCIPAL", "HOD"])
        return Identity(
            id=self.person.id,
            key=self.person.staff_key,
            mode="LOCAL_DEMO" if self.demo else "INSTITUTIONAL",
            name=self.person.display_name,
            role=self.primary_role,
            department=self.department.name,
            person_id=self.person.id,
            roles=self.roles,
            department_ids=self.scopes,
            can_manage_people="ADMIN" in self.roles,
            can_read_directory=bool(set(self.roles) & {"ADMIN", "PRINCIPAL", "HOD"}),
            applicant_eligible=self.episode.is_faculty and not exempt,
        )


def authority(
    db: Session,
    demo: DemoIdentity | None,
    session: AuthSession | InstitutionalSession,
    now: datetime | None = None,
) -> Actor:
    now = now or datetime.now(UTC)
    today = now.astimezone(ZoneInfo("Asia/Kolkata")).date()
    person = (
        db.scalar(select(Person).where(Person.demo_identity_id == demo.id))
        if demo
        else db.get(Person, session.person_id)
        if isinstance(session, InstitutionalSession)
        else None
    )
    if person is None or not person.enabled:
        raise HTTPException(403, "STAFF_NOT_PROVISIONED")
    episode = db.scalar(
        select(EmploymentEpisode).where(
            EmploymentEpisode.person_id == person.id,
            EmploymentEpisode.starts_on <= today,
            or_(EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > today),
        )
    )
    if episode is None:
        raise HTTPException(403, "EMPLOYMENT_INACTIVE")
    assignment = db.scalar(
        select(DepartmentAssignment).where(
            DepartmentAssignment.episode_id == episode.id,
            DepartmentAssignment.starts_on <= today,
            or_(
                DepartmentAssignment.ends_before.is_(None), DepartmentAssignment.ends_before > today
            ),
        )
    )
    department = db.get(Department, assignment.department_id) if assignment else None
    if department is None:
        raise HTTPException(403, "HOME_DEPARTMENT_MISSING")
    offices = list(
        db.scalars(
            select(OfficeAppointment).where(
                OfficeAppointment.person_id == person.id,
                OfficeAppointment.superseded.is_(False),
                OfficeAppointment.valid_from <= now,
                or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now),
            )
        )
    )
    roles = ["FACULTY"] if episode.is_faculty else []
    roles += sorted({"HOD" if o.office == "ACTING_HOD" else o.office for o in offices})
    if "DRC_HEAD" in roles and ("HOD" in roles or not episode.is_faculty):
        raise HTTPException(403, "CONFLICTING_AUTHORITY")
    if "PRINCIPAL" in roles and any(r in roles for r in ["HOD", "DRC_HEAD"]):
        raise HTTPException(423, "AUTHORITY_POLICY_PENDING")
    admin = db.scalar(
        select(AdministrativeGrant).where(
            AdministrativeGrant.person_id == person.id,
            AdministrativeGrant.valid_from <= now,
            or_(AdministrativeGrant.valid_until.is_(None), AdministrativeGrant.valid_until > now),
        )
    )
    if admin:
        roles.append("ADMIN")
    return Actor(
        session,
        demo,
        person,
        episode,
        department,
        offices,
        roles,
        sorted({o.department_id for o in offices if o.department_id}, key=str),
    )


def current_actor(request: Request, db: DB) -> Actor:
    if not request.app.state.settings.demo_enabled:
        token = request.cookies.get("akus_session")
        session = db.get(InstitutionalSession, digest(token)) if token else None
        if session is None or session.expires_at <= datetime.now(UTC):
            raise HTTPException(401, "AUTHENTICATION_REQUIRED")
        link = db.get(ExternalIdentity, session.external_identity_id)
        if link is None or link.revoked_at is not None or link.person_id != session.person_id:
            db.delete(session)
            db.commit()
            raise HTTPException(401, "AUTHENTICATION_REQUIRED")
        try:
            return authority(db, None, session)
        except HTTPException:
            db.delete(session)
            db.commit()
            raise
    result = resolve(db, request.cookies.get(COOKIE))
    if result is None:
        raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    try:
        return authority(db, result[1], result[0])
    except HTTPException as exc:
        if exc.detail in {"EMPLOYMENT_INACTIVE", "STAFF_NOT_PROVISIONED"}:
            db.delete(result[0])
            db.commit()
        raise


Current = Annotated[Actor, Depends(current_actor)]
