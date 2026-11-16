from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.models import AcademicYear
from akus.people.models import Department, EmploymentEpisode, Person
from akus.people.router import mutation_guard
from akus.people.schemas import CommandResult
from akus.people.service import require_admin, staff_scope
from akus.sources import imports, service
from akus.sources.models import (
    SourceImport,
    SourceRevision,
    Subject,
    SubjectAlias,
    TeachingAssignment,
)
from akus.sources.schemas import ReferenceWrite, SourceChange, TeachingWrite

router = APIRouter(prefix="/api/v1", tags=["Institutional sources"])


@router.get("/sources/reference")
def references(db: DB, actor: Current) -> dict[str, Any]:
    return {
        "departments": [
            {
                "id": d.id,
                "code": d.code,
                "name": d.name,
                "version": service.revision(db, d.__tablename__, d.id),
            }
            for d in db.scalars(select(Department).order_by(Department.code))
        ],
        "subjects": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "source_reference": s.source_reference,
                "version": service.revision(db, s.__tablename__, s.id),
            }
            for s in db.scalars(select(Subject).order_by(Subject.code))
        ],
        "aliases": [
            {
                "id": a.id,
                "alias": a.alias,
                "version": service.revision(db, a.__tablename__, a.id),
                "subject_id": a.subject_id,
                "source_reference": a.source_reference,
            }
            for a in db.scalars(select(SubjectAlias).order_by(SubjectAlias.alias))
        ],
        "years": [
            {
                "id": y.id,
                "label": y.label,
                "starts_on": y.starts_on,
                "ends_on": y.ends_on,
                "source": y.source,
            }
            for y in db.scalars(select(AcademicYear).order_by(AcademicYear.starts_on.desc()))
        ],
    }


@router.post("/admin/reference", response_model=CommandResult)
def write_reference(
    body: ReferenceWrite,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_reference(db, actor, idempotency_key, body)


@router.get("/people/staff/{person_id}/sources")
def staff_sources(person_id: UUID, db: DB, actor: Current) -> dict[str, Any]:
    return service.staff_sources(db, actor, person_id)


@router.post("/admin/staff/{person_id}/sources", response_model=CommandResult)
def change_source(
    person_id: UUID,
    body: SourceChange,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.change_source(
        db, actor, idempotency_key, person_id, body, request.app.state.settings
    )


@router.get("/teaching")
def teaching(
    db: DB,
    actor: Current,
    person_id: UUID | None = None,
    department_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    subject_id: UUID | None = None,
    q: str = Query("", max_length=100),
    term: str = Query("", max_length=60),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    query = service.scoped_teaching(db, actor)
    if q:
        query = query.join(Person, Person.id == EmploymentEpisode.person_id).where(
            Person.display_name.icontains(q, autoescape=True)
        )
    if term:
        query = query.where(TeachingAssignment.term == term)
    if person_id:
        query = query.where(EmploymentEpisode.person_id == person_id)
    for field, value in [
        (TeachingAssignment.department_id, department_id),
        (TeachingAssignment.academic_year_id, academic_year_id),
        (TeachingAssignment.subject_id, subject_id),
    ]:
        if value:
            query = query.where(field == value)
    return {
        "items": [
            service.teaching_view(db, t)
            for t in db.scalars(
                query.order_by(TeachingAssignment.starts_on.desc(), TeachingAssignment.id)
                .offset(offset)
                .limit(limit)
            )
        ],
        "total": db.scalar(select(func.count()).select_from(query.subquery())) or 0,
        "offset": offset,
        "limit": limit,
    }


@router.get("/teaching/{record_id}")
def teaching_detail(record_id: UUID, db: DB, actor: Current) -> dict[str, Any]:
    record = db.scalar(service.scoped_teaching(db, actor).where(TeachingAssignment.id == record_id))
    if not record:
        raise HTTPException(404, "NOT_FOUND")
    history = db.scalars(
        select(SourceRevision)
        .where(
            SourceRevision.entity_type == TeachingAssignment.__tablename__,
            SourceRevision.entity_id == record_id,
        )
        .order_by(SourceRevision.recorded_at.desc())
        .limit(100)
    )
    return service.teaching_view(db, record) | {
        "history": [
            {
                "id": r.id,
                "before": r.before,
                "after": r.after,
                "context": r.context,
                "recorded_at": r.recorded_at,
            }
            for r in history
        ]
    }


@router.post("/admin/teaching", response_model=CommandResult)
def add_teaching(
    body: TeachingWrite,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_teaching(db, actor, idempotency_key, body)


@router.post("/admin/teaching/{record_id}", response_model=CommandResult)
def correct_teaching(
    record_id: UUID,
    body: TeachingWrite,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_teaching(db, actor, idempotency_key, body, record_id)


def import_view(record: SourceImport, include_rows: bool = True) -> dict[str, Any]:
    result = {
        "id": record.id,
        "kind": record.kind,
        "filename": record.filename,
        "source_reference": record.source_reference,
        "status": record.status,
        "recorded_at": record.recorded_at,
        "committed_at": record.committed_at,
        "row_count": len(record.rows),
        "error_count": sum(bool(r["errors"]) for r in record.rows),
    }
    return result | ({"rows": record.rows} if include_rows else {})


@router.get("/admin/imports")
def import_list(db: DB, actor: Current, offset: int = Query(0, ge=0)) -> dict[str, Any]:
    require_admin(actor)
    return {
        "items": [
            import_view(r, False)
            for r in db.scalars(
                select(SourceImport)
                .order_by(SourceImport.recorded_at.desc(), SourceImport.id)
                .offset(offset)
                .limit(25)
            )
        ],
        "total": db.scalar(select(func.count()).select_from(SourceImport)) or 0,
    }


@router.get("/admin/imports/{record_id}")
def import_detail(record_id: UUID, db: DB, actor: Current) -> dict[str, Any]:
    require_admin(actor)
    record = db.get(SourceImport, record_id)
    if not record:
        raise HTTPException(404, "NOT_FOUND")
    return import_view(record)


@router.post("/admin/imports", status_code=201)
def stage_import(
    request: Request,
    db: DB,
    actor: Current,
    kind: Annotated[str, Form()],
    source_reference: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    mutation_guard(request, actor)
    content = file.file.read(4 * 1024 * 1024 + 1)
    return import_view(
        imports.stage(
            db,
            actor,
            kind,
            file.filename or "",
            content,
            source_reference,
            request.app.state.settings,
        )
    )


class CommitImport(BaseModel):
    confirm_authoritative_source: bool


@router.post("/admin/imports/{record_id}/commit")
def commit_import(
    record_id: UUID, body: CommitImport, request: Request, db: DB, actor: Current
) -> dict[str, Any]:
    mutation_guard(request, actor)
    if not body.confirm_authoritative_source:
        raise HTTPException(422, "SOURCE_CONFIRMATION_REQUIRED")
    return import_view(imports.commit(db, actor, record_id, request.app.state.settings))


@router.get("/dashboard")
def dashboard(db: DB, actor: Current) -> dict[str, Any]:
    from akus.identity.models import AccountRequest

    now = datetime.now(UTC)
    people = staff_scope(actor, now)
    allocations = service.scoped_teaching(db, actor).where(TeachingAssignment.voided.is_(False))
    result: dict[str, Any] = {
        "role": actor.primary_role,
        "staff_in_scope": db.scalar(select(func.count()).select_from(people.subquery())) or 0,
        "teaching_records": db.scalar(select(func.count()).select_from(allocations.subquery()))
        or 0,
        "applicant_eligible": actor.view().applicant_eligible,
        "own_review_route": ["HOD"]
        if "DRC_HEAD" in actor.roles
        else ["DRC_HEAD", "HOD"]
        if actor.view().applicant_eligible
        else [],
        "academic_status": "NOT_IMPLEMENTED",
        "teaching_acceptance": "POLICY_PENDING:IO-02",
    }
    if "ADMIN" in actor.roles:
        result["pending_accounts"] = (
            db.scalar(
                select(func.count())
                .select_from(AccountRequest)
                .where(AccountRequest.status == "PENDING")
            )
            or 0
        )
        result["staged_imports"] = (
            db.scalar(
                select(func.count())
                .select_from(SourceImport)
                .where(SourceImport.status != "COMMITTED")
            )
            or 0
        )
    if "PRINCIPAL" in actor.roles:
        # Source inventory, not inferred academic compliance percentages.
        result["departments"] = [
            {"id": d.id, "name": d.name, "teaching_records": count}
            for d, count in db.execute(
                select(Department, func.count(TeachingAssignment.id))
                .outerjoin(
                    TeachingAssignment,
                    (TeachingAssignment.department_id == Department.id)
                    & TeachingAssignment.voided.is_(False),
                )
                .group_by(Department.id)
                .order_by(Department.name)
            )
        ]
    return result


@router.get("/academic/integration/{area}")
def academic_integration(area: str, actor: Current) -> dict[str, Any]:
    if area in {"applications", "compliance"}:
        if not actor.view().applicant_eligible:
            raise HTTPException(403, "FACULTY_APPLICANT_REQUIRED_EXEMPT_OFFICE")
        phase, dependency = (
            "3–4" if area == "applications" else "6",
            "Published quota and atomic admission"
            if area == "applications"
            else "Verified examination evidence and approved teaching acceptance",
        )
    elif area == "reviews":
        if not set(actor.roles) & {"DRC_HEAD", "HOD"}:
            raise HTTPException(403, "ACADEMIC_OFFICE_REQUIRED")
        phase, dependency = (
            "4",
            "Submitted applications, independent review tasks and current office authority",
        )
    elif area == "quotas":
        if "HOD" not in actor.roles:
            raise HTTPException(403, "HOD_AUTHORITY_REQUIRED")
        phase, dependency = (
            "3",
            "Canonical NPTEL catalog, approved primary topic mappings and published annual pools",
        )
    elif area == "reports":
        if not set(actor.roles) & {"PRINCIPAL", "HOD"}:
            raise HTTPException(403, "OVERSIGHT_AUTHORITY_REQUIRED")
        phase, dependency = (
            "6–8",
            "Verified academic evidence, compliance assessments and immutable reporting snapshots",
        )
    else:
        raise HTTPException(404, "NOT_FOUND")
    return {
        "area": area,
        "status": "NOT_IMPLEMENTED",
        "phase": phase,
        "dependency": dependency,
        "records": None,
        "can_decide": False,
        "policy": "No academic state is inferred from missing records",
    }
