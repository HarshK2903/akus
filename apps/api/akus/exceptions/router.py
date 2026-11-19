from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import Select, func, or_, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.applications.models import Allocation, Application, Reconciliation, Submission
from akus.catalog.models import Offering
from akus.catalog.router import Key, mutation_guard
from akus.exceptions import history, reviewer, service
from akus.exceptions.models import (
    CaseEvent,
    Departure,
    HistoricalMandate,
    IntegrityMandate,
    SeparationSnapshot,
)
from akus.exceptions.schemas import CertificateProof, Closure, Order, RosterProof, SubjectProof
from akus.people.models import Person
from akus.people.schemas import CommandResult

router = APIRouter(prefix="/api/v1", tags=["Exceptional cases"])


@router.post("/admin/employment-episodes/{eid}/permanent-separation")
def permanent(
    eid: UUID, body: Order, db: DB, actor: Current, key: Key, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return service.record_order(db, actor, key, eid, body, request.app.state.settings)


def kind(request: Request) -> str:
    return "SEPARATION" if "/separation-cases" in request.url.path else "INTEGRITY"


def scoped(db: DB, actor: Current, category: str) -> Select[tuple[Reconciliation]]:
    query = select(Reconciliation).join(Application).where(Reconciliation.kind == category)
    if "PRINCIPAL" in actor.roles:
        return query
    departments = [o.department_id for o in actor.offices if o.office in {"HOD", "ACTING_HOD"}]
    now = datetime.now(UTC)
    model = HistoricalMandate if category == "SEPARATION" else IntegrityMandate
    authorized = select(model.case_id).where(
        model.reviewer_id == actor.person.id,
        model.revoked_at.is_(None),
        model.valid_from <= now,
        model.valid_until > now,
    )
    if not departments and not db.scalar(authorized.limit(1)):
        raise HTTPException(403, "CASE_ACCESS_DENIED")
    return query.where(
        or_(
            Application.department_id.in_(departments),
            Reconciliation.id.in_(authorized),
        )
    )


def view(db: DB, c: Reconciliation, actor: Current, detail: bool = False) -> dict[str, Any]:
    app = db.get(Application, c.application_id)
    assert app
    person, run = db.get(Person, app.person_id), db.get(Offering, app.offering_id)
    result = {
        "id": c.id,
        "app_id": app.id,
        "applicant": person.display_name if person else None,
        "offering": run.provider_id if run else None,
        "status": c.status,
        "reason": c.reason,
        "kind": c.kind,
        "updated_at": c.updated_at,
    }
    if not detail:
        return result
    allocation = db.get(Allocation, app.id)
    sub = db.get(Submission, app.id)
    events = list(
        db.scalars(
            select(CaseEvent).where(CaseEvent.case_id == c.id).order_by(CaseEvent.version.desc())
        )
    )
    order = db.scalar(select(Departure).where(Departure.episode_id == app.episode_id))
    snapshot = db.get(SeparationSnapshot, order.id) if order else None
    grant = history.authorized(db, actor, c, app) if c.kind == "SEPARATION" else None
    return result | {
        "may_verify_absence": c.kind == "SEPARATION"
        and c.status == "OPEN"
        and c.reason == "ENROLLMENT_CHRONOLOGY_REQUIRED"
        and history.authorized(db, actor, c, app, "ENROLLMENT_ABSENCE") is not None,
        "may_verify_certificate": grant is not None and app.state == "SEPARATED",
        "designated_subject_id": grant.subject_id if grant else None,
        "other_open_reviews": [
            r.reason
            for r in db.scalars(
                select(Reconciliation).where(
                    Reconciliation.application_id == app.id,
                    Reconciliation.id != c.id,
                    Reconciliation.status == "OPEN",
                )
            )
        ],
        "state": app.state,
        "submitted_at": app.submitted_at,
        "current_pool": allocation.pool_id if allocation else None,
        "allocation": allocation.state if allocation else None,
        "original_pool": sub.original_pool_id if sub else None,
        "facts": c.context,
        "events": [
            {
                "id": e.id,
                "action": e.action,
                "version": e.version,
                "recorded_at": e.recorded_at,
                "facts": e.facts,
                "actor": e.actor_id,
                "office": e.office_id,
            }
            for e in events
        ],
        "subjects_at_separation": snapshot.subjects if snapshot and c.kind == "SEPARATION" else [],
        "can_decide": c.status == "OPEN"
        and app.person_id != actor.person.id
        and (
            service.mandate(db, actor, c, app) is not None
            if c.kind == "INTEGRITY"
            else any(
                o.department_id == app.department_id and o.office in {"HOD", "ACTING_HOD"}
                for o in actor.offices
            )
            and c.reason
            in {"Q44_HOD_REVIEW", "ENROLLMENT_CHRONOLOGY_REQUIRED", "Q47_CHRONOLOGY_REVIEW"}
        ),
    }


@router.get("/integrity-cases")
@router.get("/separation-cases")
def listing(
    db: DB,
    actor: Current,
    request: Request,
    status: Literal["OPEN", "RESOLVED", "ALL"] = "OPEN",
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    query = scoped(db, actor, kind(request))
    if status != "ALL":
        query = query.where(Reconciliation.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {
        "items": [
            view(db, c, actor)
            for c in db.scalars(
                query.order_by(Reconciliation.updated_at.desc(), Reconciliation.id)
                .offset(offset)
                .limit(25)
            )
        ],
        "total": total,
    }


@router.get("/integrity-cases/{cid}")
@router.get("/separation-cases/{cid}")
def detail(cid: UUID, db: DB, actor: Current, request: Request) -> dict[str, Any]:
    c = db.scalar(scoped(db, actor, kind(request)).where(Reconciliation.id == cid))
    if not c:
        raise HTTPException(404, "CASE_NOT_FOUND")
    return view(db, c, actor, True)


@router.post("/integrity-cases/{cid}/decision")
@router.post("/separation-cases/{cid}/decision")
def decision(
    cid: UUID, body: Closure, db: DB, actor: Current, request: Request, key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.decide(db, actor, key, cid, kind(request), body, request.app.state.settings)


@router.get("/separation-cases/{cid}/historical-review")
def historical_report(
    cid: UUID, db: DB, actor: Current, as_of: datetime | None = None
) -> dict[str, Any]:
    case = db.scalar(scoped(db, actor, "SEPARATION").where(Reconciliation.id == cid))
    if not case:
        raise HTTPException(404, "CASE_NOT_FOUND")
    app = db.get(Application, case.application_id)
    assert app
    return history.report(db, app, as_of or datetime.now(UTC))


@router.post("/separation-cases/{cid}/historical-review")
def verify_historical(
    cid: UUID, body: CertificateProof, db: DB, actor: Current, request: Request, key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return history.record(db, actor, key, cid, body)


@router.get("/review-office-alerts")
def office_alerts(
    db: DB, actor: Current, offset: int = Query(0, ge=0), vacant_only: bool = True
) -> dict[str, Any]:
    return reviewer.pending(db, actor, offset, vacant_only)


@router.post("/separation-cases/{cid}/roster-finding")
def absence(
    cid: UUID, body: RosterProof, db: DB, actor: Current, request: Request, key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.verify_absence(db, actor, key, cid, body, request.app.state.settings)


@router.post("/separation-cases/{cid}/historical-review/subject")
def historical_subject(
    cid: UUID, body: SubjectProof, db: DB, actor: Current, request: Request, key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return history.verify_subject(db, actor, key, cid, body)
