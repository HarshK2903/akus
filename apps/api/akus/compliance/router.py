from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import Boolean, Date, Select, String, cast, func, or_, select, true
from starlette.exceptions import HTTPException

from akus.access import DB, Actor, Current
from akus.applications.models import Allocation, Application, Reconciliation
from akus.applications.service import today
from akus.catalog import common
from akus.catalog.models import Course, Offering
from akus.catalog.router import Key, mutation_guard
from akus.compliance import assessment, credentials
from akus.compliance.models import AssessmentSnapshot, CredentialDocument, CredentialEvent
from akus.compliance.schemas import Capture, Disposition, ExamProof, Registration, Verify
from akus.exceptions.models import CaseEvent, Departure, HistoricalFinding, SeparationSnapshot
from akus.exceptions.schemas import IST
from akus.exceptions.service import exclusive
from akus.models import AcademicYear
from akus.people.models import DepartmentAssignment, EmploymentEpisode, Person
from akus.people.schemas import CommandResult
from akus.sources.models import SourceRevision, Subject

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
def download(
    aid: UUID, did: UUID, db: DB, actor: Current, revision: UUID | None = None
) -> Response:
    actor = common.refresh(db, actor)
    app = db.get(Application, aid)
    if not app or (actor.person.id != app.person_id and not credentials.grant(db, actor, app)):
        raise HTTPException(403, "PRIVATE_CREDENTIAL_DOCUMENT")
    doc = db.get(CredentialDocument, did)
    if not doc or doc.application_id != aid:
        raise HTTPException(404, "DOCUMENT_NOT_FOUND")
    scan = doc.scan
    if revision is not None:
        event = db.get(CredentialEvent, revision)
        if not event or event.application_id != aid or event.document_id != did:
            raise HTTPException(404, "DOCUMENT_REVISION_NOT_FOUND")
        scan = event.facts.get("document_scan", scan)
    if scan != "CLEAN":
        raise HTTPException(423, "DOCUMENT_QUARANTINED_AWAITING_SCAN")
    common.event(
        db,
        actor,
        did,
        "PRIVATE_CREDENTIAL_DOWNLOAD",
        {"application_id": str(aid), "revision": str(revision) if revision else None},
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


def episodes(
    actor: Actor, scope: str, historical: bool = False, department: UUID | None = None
) -> Select[tuple[EmploymentEpisode]]:
    q = select(EmploymentEpisode)
    if not historical:
        q = q.where(EmploymentEpisode.is_faculty.is_(True), EmploymentEpisode.starts_on <= today())
    if scope == "personal":
        common.require_applicant(actor)
        return q.where(EmploymentEpisode.person_id == actor.person.id)
    if scope == "institution" and "PRINCIPAL" in actor.roles and department is None:
        return q
    if (scope == "department" and "HOD" in actor.roles) or (
        scope == "institution" and "PRINCIPAL" in actor.roles
    ):
        permitted = actor.scopes if scope == "department" else [department] if department else []
        if department is not None and department not in permitted:
            raise HTTPException(403, "DEPARTMENT_ACCESS_DENIED")
        # The last effective posting for a closed episode, current posting for active staff.
        effective_date = func.least(
            today(), func.coalesce(EmploymentEpisode.ends_before - 1, today())
        )
        return q.where(
            select(DepartmentAssignment.id)
            .where(
                DepartmentAssignment.episode_id == EmploymentEpisode.id,
                DepartmentAssignment.department_id.in_([department] if department else permitted),
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
    department: UUID | None = None,
    search: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    q = episodes(actor, scope, department=department).join(
        Person, Person.id == EmploymentEpisode.person_id
    )
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
    department: UUID | None = None,
    as_of: datetime | None = None,
    search: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
) -> dict[str, Any]:
    actor = report_reader(db, actor)
    q = episodes(
        actor,
        scope,
        historical=bool(as_of),
        department=None if as_of and scope == "institution" else department,
    ).join(Person, Person.id == EmploymentEpisode.person_id)
    name_col = Person.display_name
    start_col, end_col = EmploymentEpisode.starts_on, EmploymentEpisode.ends_before
    if as_of:
        if not as_of.tzinfo or as_of > datetime.now(UTC):
            raise HTTPException(422, "VALID_HISTORICAL_INSTANT_REQUIRED")

        # Reconstruct source membership and search labels at the knowledge cutoff.
        # Earlier installations can predate the revision trigger; their first
        # correction's before-image is the baseline for the earlier interval.
        def source_at(model: type[Person] | type[EmploymentEpisode]) -> Any:
            scoped = select(SourceRevision).where(
                SourceRevision.entity_type == model.__tablename__,
                SourceRevision.entity_id == model.id,
            )
            before = (
                scoped.with_only_columns(SourceRevision.before)
                .where(SourceRevision.recorded_at > as_of)
                .order_by(SourceRevision.recorded_at, SourceRevision.id)
                .limit(1)
                .scalar_subquery()
                .correlate(model)
            )
            after = (
                scoped.with_only_columns(SourceRevision.after)
                .where(SourceRevision.recorded_at <= as_of)
                .order_by(SourceRevision.recorded_at.desc(), SourceRevision.id.desc())
                .limit(1)
                .scalar_subquery()
                .correlate(model)
            )
            return (
                select(
                    func.coalesce(
                        after,
                        before,
                        func.jsonb_build_object("display_name", Person.display_name)
                        if model is Person
                        else func.jsonb_build_object(
                            "starts_on",
                            EmploymentEpisode.starts_on,
                            "ends_before",
                            EmploymentEpisode.ends_before,
                            "is_faculty",
                            EmploymentEpisode.is_faculty,
                        ),
                    ).label("facts")
                )
                .correlate(model)
                .lateral()
            )

        e, p = source_at(EmploymentEpisode), source_at(Person)
        q = q.join(e, true()).join(p, true())
        start_col = cast(e.c.facts.op("->>")("starts_on"), Date)  # type: ignore[assignment]
        end_col = cast(e.c.facts.op("->>")("ends_before"), Date)  # type: ignore[assignment]
        name_col = p.c.facts.op("->>")("display_name")
        q = q.where(
            EmploymentEpisode.recorded_at <= as_of,
            start_col <= as_of.astimezone(IST).date(),
            cast(e.c.facts.op("->>")("is_faculty"), Boolean),
        )
        if department is not None or scope == "department":
            # The source trigger records the complete posting after every insertion
            # and correction. Select its latest known version before filtering the
            # department, or a later transfer could erase historical membership.
            postings = (
                select(SourceRevision.entity_id, SourceRevision.after.label("facts"))
                .where(
                    SourceRevision.entity_type == DepartmentAssignment.__tablename__,
                    SourceRevision.recorded_at <= as_of,
                )
                .distinct(SourceRevision.entity_id)
                .order_by(
                    SourceRevision.entity_id,
                    SourceRevision.recorded_at.desc(),
                    SourceRevision.id.desc(),
                )
                .subquery()
            )
            facts = postings.c.facts
            cutoff = as_of.astimezone(IST).date()
            effective = func.least(cutoff, func.coalesce(end_col - 1, cutoff))
            permitted = [str(department)] if department else [str(d) for d in actor.scopes]
            q = q.where(
                select(postings.c.entity_id)
                .where(
                    facts["episode_id"].astext == cast(EmploymentEpisode.id, String),
                    facts["department_id"].astext.in_(permitted),
                    cast(facts["starts_on"].astext, Date) <= effective,
                    or_(
                        facts["ends_before"].astext.is_(None),
                        cast(facts["ends_before"].astext, Date) > effective,
                    ),
                )
                .exists()
            )
    if search.strip():
        q = q.where(name_col.icontains(search.strip(), autoescape=True))
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
            start_col <= year.ends_on,
            or_(
                end_col.is_(None),
                end_col > year.starts_on,
            ),
        )
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = []
    for ep, name in db.execute(
        q.add_columns(name_col)
        .order_by(name_col, start_col.desc(), EmploymentEpisode.id)
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


@router.get("/me/employment-episodes/{eid}/history")
def employment_history(
    eid: UUID,
    db: DB,
    actor: Current,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
) -> dict[str, Any]:
    actor = report_reader(db, actor)
    ep = db.scalar(episodes(actor, "personal").where(EmploymentEpisode.id == eid))
    if not ep:
        raise HTTPException(404, "EPISODE_OUTSIDE_REPORT_SCOPE")
    order = db.scalar(select(Departure).where(Departure.episode_id == eid))
    frozen = db.get(SeparationSnapshot, order.id) if order else None
    q = select(Application).where(Application.episode_id == ep.id)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.execute(
        q.join(Course, Course.id == Application.course_id)
        .outerjoin(Allocation, Allocation.application_id == Application.id)
        .add_columns(Course.title, Allocation.state)
        .order_by(Application.created_at.desc(), Application.id)
        .offset(offset)
        .limit(limit)
    )
    items = []
    for app, course, allocation in rows:
        event = db.scalar(
            select(CaseEvent)
            .join(Reconciliation)
            .where(
                Reconciliation.application_id == app.id,
                CaseEvent.action.in_(["Q43", "Q44", "Q45", "Q47", "INVALIDATE"]),
            )
            .order_by(CaseEvent.recorded_at.desc())
            .limit(1)
        )
        items.append(
            {
                "id": app.id,
                "course": course,
                "state": app.state,
                "allocation": allocation,
                "closure": event.action if event else None,
                "decided_at": event.recorded_at if event else None,
            }
        )
    return {
        "starts_on": ep.starts_on,
        "ends_before": ep.ends_before,
        "source_reference": ep.source_reference,
        "recorded_at": ep.recorded_at,
        "order": {
            "effective_on": order.effective_on,
            "effective_at": order.effective_at,
            "recorded_at": order.recorded_at,
            "source_reference": order.proof["source_reference"],
        }
        if order
        else None,
        "frozen_at": frozen.recorded_at if frozen else None,
        "frozen_subjects": [
            item | {"subject": db.get_one(Subject, UUID(item["subject_id"])).name}
            for item in frozen.subjects
        ]
        if frozen
        else [],
        "total": total,
        "items": items,
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
    ep = db.scalar(
        episodes(actor, scope, historical=bool(snapshot_id)).where(EmploymentEpisode.id == eid)
    )
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
