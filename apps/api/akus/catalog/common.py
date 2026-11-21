"""Academic commands share source-authority protection; resources use scoped row locks."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor, authority
from akus.catalog.models import AcademicEvent, ProviderSnapshot
from akus.catalog.provider import BASE_URL
from akus.identity.models import ExternalIdentity, InstitutionalSession
from akus.models import AuditEvent, AuthSession
from akus.people.models import CommandReceipt, OfficeAppointment
from akus.people.schemas import CommandResult
from akus.people.service import replay as source_replay
from akus.people.service import request_digest


def receipt_operation(operation: str) -> str:
    return (
        operation if len(operation) <= 80 else "ACADEMIC:" + sha256(operation.encode()).hexdigest()
    )


def replay(
    db: Session, actor: Actor, key: UUID, operation: str, body: BaseModel
) -> CommandResult | None:
    return source_replay(db, actor, key, receipt_operation(operation), body)


def require_person_evidence(db: Session, reference: str, digest: str) -> None:
    endpoint = reference.split("?", 1)[0].split("#", 1)[0].rstrip("/").casefold()
    if endpoint == BASE_URL.casefold() or db.scalar(
        select(ProviderSnapshot.id).where(ProviderSnapshot.digest == digest).limit(1)
    ):
        raise HTTPException(422, "PUBLIC_COURSE_METADATA_IS_NOT_PERSON_EVIDENCE")


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def refresh(db: Session, actor: Actor, key: UUID | None = None) -> Actor:
    # Shared gate allows concurrent academics; exclusive source corrections cannot
    # revoke an appointment halfway through an authorized academic transaction.
    person_id, token_hash = actor.person.id, actor.session.token_hash
    institutional = isinstance(actor.session, InstitutionalSession)
    db.execute(text("SELECT pg_advisory_xact_lock_shared(8210402)"))
    if key:
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"command:{person_id}:{key}"},
        )
    db.expire_all()
    session = (
        db.get(InstitutionalSession, token_hash)
        if institutional
        else db.get(AuthSession, token_hash)
    )
    if session is None or session.expires_at <= datetime.now(UTC):
        raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    if isinstance(session, InstitutionalSession):
        link = db.get(ExternalIdentity, session.external_identity_id)
        if not link or link.revoked_at or link.person_id != person_id:
            raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    return authority(db, actor.demo, session)


def department_scope(actor: Actor, department: UUID) -> None:
    if "PRINCIPAL" in actor.roles or "ADMIN" in actor.roles:
        return
    if department == actor.department.id or department in actor.scopes:
        return
    raise HTTPException(403, "DEPARTMENT_ACCESS_DENIED")


def require_hod(actor: Actor, department: UUID) -> OfficeAppointment:
    for office in actor.offices:
        if office.office in {"HOD", "ACTING_HOD"} and office.department_id == department:
            return office
    raise HTTPException(403, "CURRENT_DEPARTMENT_HOD_REQUIRED")


def require_applicant(actor: Actor) -> None:
    if not actor.view().applicant_eligible:
        raise HTTPException(403, "ELIGIBLE_FACULTY_OR_DRC_REQUIRED")


def event(
    db: Session,
    actor: Actor,
    entity: UUID,
    kind: str,
    data: dict[str, Any],
    department: UUID | None = None,
) -> None:
    db.add(
        AcademicEvent(
            entity_id=entity,
            kind=kind,
            actor_id=actor.person.id,
            department_id=department,
            data=data,
        )
    )
    db.add(
        AuditEvent(
            actor_id=actor.demo.id if actor.demo else None,
            action=kind,
            details={
                "entity_id": str(entity),
                "actor_person_id": str(actor.person.id),
                "roles": ",".join(actor.roles),
                "department_id": str(department or ""),
                "policy": "V2.4/V2.3",
            },
        )
    )


def finish(
    db: Session,
    actor: Actor,
    key: UUID,
    operation: str,
    body: BaseModel,
    entity: UUID,
    data: dict[str, Any],
    department: UUID | None = None,
) -> CommandResult:
    event(db, actor, entity, operation.split(":")[0], data, department)
    db.add(
        CommandReceipt(
            actor_id=actor.person.id,
            key=key,
            operation=receipt_operation(operation),
            request_hash=request_digest(body),
            result={"id": str(entity)},
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "ACADEMIC_RECORD_CONFLICT") from exc
    return CommandResult(id=entity)


def history(db: Session, entity: UUID) -> list[dict[str, Any]]:
    return [
        {
            "id": row.id,
            "kind": row.kind,
            "actor_id": row.actor_id,
            "recorded_at": row.recorded_at,
            "data": row.data,
        }
        for row in db.scalars(
            select(AcademicEvent)
            .where(AcademicEvent.entity_id == entity)
            .order_by(AcademicEvent.recorded_at.desc())
            .limit(100)
        )
    ]


__all__ = [
    "normalize",
    "refresh",
    "department_scope",
    "require_hod",
    "require_person_evidence",
    "require_applicant",
    "event",
    "finish",
    "history",
    "replay",
]
