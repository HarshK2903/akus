from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import Select, func, or_, select
from starlette.exceptions import HTTPException

from akus.access import DB, Actor, Current
from akus.applications.models import Application
from akus.applications.service import today
from akus.catalog import common
from akus.catalog.models import Course, Offering
from akus.catalog.router import Key, mutation_guard
from akus.compliance import assessment, credentials
from akus.compliance.models import AssessmentSnapshot, CredentialDocument, CredentialEvent
from akus.compliance.schemas import Capture, Disposition, ExamProof, Registration, Verify
from akus.exceptions.models import HistoricalFinding
from akus.exceptions.service import exclusive
from akus.models import AcademicYear
from akus.people.models import DepartmentAssignment, EmploymentEpisode, Person
from akus.people.schemas import CommandResult

router = APIRouter(prefix="/api/v1", tags=["Verified credentials and academic compliance"])


@router.get("/certificates")
def library(
    db: DB,
    actor: Current,
    search: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    pending: bool = False,
) -> dict[str, Any]:
    q = (
        credentials.scope(actor)
        .join(Course, Course.id == Application.course_id)
        .join(Person, Person.id == Application.person_id)
    )
    state = (
        select(CredentialEvent.kind)
        .where(CredentialEvent.application_id == Application.id)
        .order_by(CredentialEvent.version.desc())
        .limit(1)
        .scalar_subquery()
    )
    if pending:
        q = q.where(state == "ASSERTED")
    if search.strip():
        q = q.where(
            or_(
                Course.title.icontains(search.strip(), autoescape=True),
                Person.display_name.icontains(search.strip(), autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = []
    for app, course, name, status in db.execute(
        q.add_columns(Course.title, Person.display_name, state)
        .order_by(Application.submitted_at.desc(), Application.id)
        .offset(offset)
        .limit(limit)
    ):
        items.append(
            {
                "id": app.id,
                "course": course,
                "person": name,
                "status": status
                or (
                    "VERIFIED"
                    if db.scalar(
                        select(HistoricalFinding.id).where(
                            HistoricalFinding.application_id == app.id
                        )
                    )
                    else "AWAITING_EVIDENCE"
                ),
                "state": app.state,
            }
        )
    return {"items": items, "total": total}


@router.get("/certificates/{aid}")
def dossier(aid: UUID, db: DB, actor: Current) -> dict[str, Any]:
    app = db.scalar(credentials.scope(actor).where(Application.id == aid))
    if not app:
        raise HTTPException(404, "CREDENTIAL_DOSSIER_NOT_FOUND")
    course = db.get(Course, app.course_id)
    offering = db.get(Offering, app.offering_id)
    return credentials.timeline(db, app, actor) | {
        "course": course.title if course else None,
        "offering": offering.provider_id if offering else None,
        "episode_id": app.episode_id,
        "state": app.state,
    }


@router.post("/certificates/{aid}/evidence")
def register(
    aid: UUID, body: Registration, key: Key, db: DB, actor: Current, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return credentials.write(db, actor, key, aid, body)


@router.post("/certificates/{aid}/exam")
def exam(
    aid: UUID, body: ExamProof, key: Key, db: DB, actor: Current, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return credentials.write(db, actor, key, aid, body)


@router.post("/certificates/{aid}/verify")
def verify(
    aid: UUID, body: Verify, key: Key, db: DB, actor: Current, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return credentials.write(db, actor, key, aid, body)


@router.post("/certificates/{aid}/disposition")
def disposition(
    aid: UUID, body: Disposition, key: Key, db: DB, actor: Current, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return credentials.write(db, actor, key, aid, body)


@router.get("/certificates/{aid}/documents/{did}")
def download(aid: UUID, did: UUID, db: DB, actor: Current) -> Response:
    actor = common.refresh(db, actor)
    app = db.get(Application, aid)
    if not app or (actor.person.id != app.person_id and not credentials.grant(db, actor, app)):
        raise HTTPException(403, "PRIVATE_CREDENTIAL_DOCUMENT")
    doc = db.get(CredentialDocument, did)
    if not doc or doc.application_id != aid:
        raise HTTPException(404, "DOCUMENT_NOT_FOUND")
    if doc.scan != "CLEAN":
        raise HTTPException(423, "DOCUMENT_QUARANTINED_AWAITING_SCAN")
    common.event(
        db,
        actor,
        did,
        "PRIVATE_CREDENTIAL_DOWNLOAD",
        {"application_id": str(aid)},
        app.department_id,
    )
    db.commit()
    return Response(
        content=doc.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="certificate.pdf"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox; default-src 'none'",
        },
    )


def episodes(actor: Actor, scope: str) -> Select[tuple[EmploymentEpisode]]:
    q = select(EmploymentEpisode).where(
        EmploymentEpisode.is_faculty.is_(True), EmploymentEpisode.starts_on <= today()
    )
    if scope == "personal":
        common.require_applicant(actor)
        return q.where(EmploymentEpisode.person_id == actor.person.id)
    if scope == "institution" and "PRINCIPAL" in actor.roles:
        return q
    if scope == "department" and "HOD" in actor.roles:
        # The last effective posting for a closed episode, current posting for active staff.
        effective_date = func.least(
            today(), func.coalesce(EmploymentEpisode.ends_before - 1, today())
        )
        return q.where(
            select(DepartmentAssignment.id)
            .where(
                DepartmentAssignment.episode_id == EmploymentEpisode.id,
                DepartmentAssignment.department_id.in_(actor.scopes),
                DepartmentAssignment.starts_on <= effective_date,
                or_(
                    DepartmentAssignment.ends_before.is_(None),
                    DepartmentAssignment.ends_before > effective_date,
                ),
            )
            .exists()
        )
    raise HTTPException(403, "COMPLIANCE_REPORT_SCOPE_DENIED")


@router.get("/compliance/episodes")
def population(
    db: DB,
    actor: Current,
    scope: Literal["personal", "department", "institution"] = "personal",
    search: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    q = episodes(actor, scope).join(Person, Person.id == EmploymentEpisode.person_id)
    if search.strip():
        q = q.where(Person.display_name.icontains(search.strip(), autoescape=True))
    return {
        "total": db.scalar(select(func.count()).select_from(q.subquery())),
        "items": [
            {"id": ep.id, "name": name, "starts_on": ep.starts_on, "ends_before": ep.ends_before}
            for ep, name in db.execute(
                q.add_columns(Person.display_name)
                .order_by(
                    Person.display_name, EmploymentEpisode.starts_on.desc(), EmploymentEpisode.id
                )
                .offset(offset)
                .limit(limit)
            )
        ],
    }


def report_reader(db: DB, actor: Actor) -> Actor:
    # Authorization and all derived facts share one consistent PostgreSQL snapshot.
    from sqlalchemy import text

    db.rollback()
    db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    return common.refresh(db, actor)


@router.get("/compliance/register")
def register_report(
    db: DB,
    actor: Current,
    scope: Literal["department", "institution"],
    kind: Literal["annual", "silver"],
    year_id: UUID | None = None,
    as_of: datetime | None = None,
    search: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
) -> dict[str, Any]:
    actor = report_reader(db, actor)
    q = episodes(actor, scope).join(Person, Person.id == EmploymentEpisode.person_id)
    if as_of:
        if not as_of.tzinfo or as_of > datetime.now(UTC):
            raise HTTPException(422, "VALID_HISTORICAL_INSTANT_REQUIRED")
        q = q.where(EmploymentEpisode.recorded_at <= as_of)
    if search.strip():
        q = q.where(Person.display_name.icontains(search.strip(), autoescape=True))
    year = (
        db.get(AcademicYear, year_id)
        if year_id
        else db.scalar(
            select(AcademicYear).where(
                AcademicYear.starts_on <= today(), AcademicYear.ends_on >= today()
            )
        )
    )
    if kind == "annual":
        if not year:
            raise HTTPException(404, "ACADEMIC_YEAR_NOT_CONFIGURED")
        q = q.where(
            EmploymentEpisode.starts_on <= year.ends_on,
            or_(
                EmploymentEpisode.ends_before.is_(None),
                EmploymentEpisode.ends_before > year.starts_on,
            ),
        )
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = []
    for ep, name in db.execute(
        q.add_columns(Person.display_name)
        .order_by(Person.display_name, EmploymentEpisode.starts_on.desc(), EmploymentEpisode.id)
        .offset(offset)
        .limit(limit)
    ):
        snap = None
        report_data = None
        if as_of:
            snap = db.scalar(
                select(AssessmentSnapshot)
                .where(
                    AssessmentSnapshot.episode_id == ep.id, AssessmentSnapshot.recorded_at <= as_of
                )
                .order_by(AssessmentSnapshot.recorded_at.desc())
                .limit(1)
            )
            if snap:
                report_data = snap.facts
        else:
            report_data = assessment.assess(db, ep)
        records = [] if report_data is None else report_data[kind]
        if kind == "annual" and year:
            records = [r for r in records if r["id"] == str(year.id)]
        items.append(
            {
                "episode_id": ep.id,
                "name": report_data["name"] if report_data else name,
                "snapshot_id": snap.id if snap else None,
                "records": [
                    {"id": r["id"], "label": r.get("subject", r.get("year")), "status": r["status"]}
                    for r in records
                ],
                "coverage": "NO_SAVED_OBSERVATION" if report_data is None else "ASSESSED",
            }
        )
    return {
        "items": items,
        "total": total,
        "year_id": year.id if year else None,
        "as_of": as_of,
        "years": [
            {"id": y.id, "label": y.label}
            for y in db.scalars(select(AcademicYear).order_by(AcademicYear.starts_on.desc()))
        ],
    }


@router.get("/compliance/episodes/{eid}")
def report(
    eid: UUID,
    db: DB,
    actor: Current,
    scope: Literal["personal", "department", "institution"] = "personal",
    snapshot_id: UUID | None = None,
) -> dict[str, Any]:
    actor = report_reader(db, actor)
    ep = db.scalar(episodes(actor, scope).where(EmploymentEpisode.id == eid))
    if not ep:
        raise HTTPException(404, "EPISODE_OUTSIDE_REPORT_SCOPE")
    snapshots = db.scalars(
        select(AssessmentSnapshot)
        .where(AssessmentSnapshot.episode_id == eid)
        .order_by(AssessmentSnapshot.recorded_at.desc())
        .limit(100)
    )
    saved = [{"id": s.id, "recorded_at": s.recorded_at, "digest": s.digest} for s in snapshots]
    if snapshot_id:
        snap = db.get(AssessmentSnapshot, snapshot_id)
        if not snap or snap.episode_id != eid:
            raise HTTPException(404, "SAVED_ASSESSMENT_NOT_FOUND")
        return snap.facts | {"as_of": snap.recorded_at, "snapshots": saved, "view": "SAVED"}
    return assessment.assess(db, ep) | {
        "as_of": datetime.now(UTC),
        "snapshots": saved,
        "view": "LATEST",
    }


@router.post("/compliance/snapshots")
def snapshot(
    body: Capture,
    key: Key,
    db: DB,
    actor: Current,
    request: Request,
    scope: Literal["personal", "department"] = "personal",
) -> CommandResult:
    mutation_guard(request, actor)
    exclusive(db)
    actor = common.refresh(db, actor, key)
    ep = db.scalar(episodes(actor, scope).where(EmploymentEpisode.id == body.episode_id))
    if not ep:
        raise HTTPException(404, "EPISODE_OUTSIDE_REPORT_SCOPE")
    op = "COMPLIANCE_CAPTURE:" + str(ep.id)
    if result := common.replay(db, actor, key, op, body):
        return result
    row = assessment.capture(db, ep)
    return common.finish(
        db, actor, key, op, body, row.id, {"episode_id": str(ep.id), "digest": row.digest}
    )
