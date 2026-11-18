from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from sqlalchemy import func, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.auth import csrf_valid
from akus.catalog import common, provider, service
from akus.catalog.models import (
    Course,
    MappingAnchor,
    MappingRequest,
    MappingRevision,
    Offering,
    ProviderFetch,
    ProviderSnapshot,
    Topic,
    TopicAlias,
    TopicProposal,
)
from akus.catalog.schemas import (
    AliasWrite,
    CourseWrite,
    DemoOffering,
    MappingIntake,
    MappingWrite,
    OfferingFetch,
    ProposalResolve,
    ProposalWrite,
    QuotaWrite,
    SnapshotAccept,
    TopicWrite,
)
from akus.models import AcademicYear
from akus.people.models import Department
from akus.people.schemas import CommandResult
from akus.people.service import require_admin
from akus.quotas.models import QuotaPool
from akus.quotas.service import pool_view, write_pool

router = APIRouter(prefix="/api/v1", tags=["NPTEL catalog and annual topic quotas"])
Key = Annotated[UUID, Header(alias="Idempotency-Key")]


def mutation_guard(request: Request, actor: Current) -> None:
    if request.headers.get("origin") != request.app.state.settings.public_origin:
        raise HTTPException(403, "ORIGIN_REJECTED")
    if not csrf_valid(actor.session, request.headers.get("x-csrf-token", "")):
        raise HTTPException(403, "CSRF_REJECTED")
    # Each command revalidates its specific source/applicant/HoD authority after locks.


def course_view(db: DB, row: Course) -> dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "title": row.title,
        "description": row.description,
        "source_reference": row.source_reference,
        "version": row.version,
    }


def offering_view(
    db: DB,
    actor: Current,
    request: Request,
    row: Offering,
    department: UUID | None = None,
    *,
    authorized_history: bool = False,
) -> dict[str, Any]:
    department = department or actor.department.id
    if not authorized_history:
        common.department_scope(actor, department)
    source = service.snapshot(db, row)
    mapping = service.current_mapping(db, department, row.course_id)
    metadata = source.metadata_json if source else None
    year = None
    if metadata and metadata.get("scheduled_exam_on"):
        scheduled_on = date.fromisoformat(metadata["scheduled_exam_on"])
        year = db.scalar(
            select(AcademicYear).where(
                AcademicYear.starts_on <= scheduled_on,
                AcademicYear.ends_on >= scheduled_on,
            )
        )
    pool = (
        db.scalar(
            select(QuotaPool).where(
                QuotaPool.department_id == department,
                QuotaPool.topic_id == mapping.topic_id,
                QuotaPool.academic_year_id == year.id,
            )
        )
        if year and mapping
        else None
    )
    blockers = []
    if row.source_status != "CURRENT" or not service.source_usable(
        source, request.app.state.settings
    ):
        blockers.append("SOURCE_MISSING_STALE_OR_UNAVAILABLE")
    if not mapping:
        blockers.append("HOD_MAPPING_REQUIRED")
    elif source and mapping.topic_id not in service.topic_candidates(db, source):
        blockers.append("PROVIDER_TAXONOMY_REVIEW_REQUIRED")
    if not year:
        blockers.append("SCHEDULED_EXAM_YEAR_NOT_CONFIGURED")
    if not pool or pool.status != "PUBLISHED":
        blockers.append("PUBLISHED_ANNUAL_QUOTA_REQUIRED")
    elif pool.occupied >= pool.maximum:
        blockers.append("QUOTA_FULL")
    return {
        "id": row.id,
        "course_id": row.course_id,
        "provider_id": row.provider_id,
        "version": row.version,
        "source_status": row.source_status,
        "snapshot_id": source.id if source else None,
        "metadata": metadata,
        "source_url": source.source_url if source else None,
        "observed_at": source.observed_at if source else None,
        "trust": source.trust if source else None,
        "fresh": service.source_usable(source, request.app.state.settings),
        "department_id": department,
        "mapping_id": mapping.mapping_id if mapping else None,
        "mapping_revision_id": mapping.id if mapping else None,
        "mapping_version": mapping.version if mapping else None,
        "topic_id": mapping.topic_id if mapping else None,
        "topic": (
            db.scalar(select(Topic.name).where(Topic.id == mapping.topic_id)) or "Unavailable"
        )
        if mapping
        else None,
        "expected_exam_year": year.label if year else None,
        "quota": pool_view(db, pool) if pool else None,
        "blockers": blockers,
        "actual_exam": "NOT_VERIFIED",
        "enrollment": "NOT_VERIFIED",
    }


@router.get("/nptel/context")
def context(db: DB, actor: Current) -> dict[str, Any]:
    query = select(Department)
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        query = query.where(Department.id.in_(set(actor.scopes) | {actor.department.id}))
    return {
        "home_department_id": actor.department.id,
        "can_source": "ADMIN" in actor.roles,
        "can_apply": actor.view().applicant_eligible,
        "hod_departments": [
            o.department_id for o in actor.offices if o.office in {"HOD", "ACTING_HOD"}
        ],
        "departments": [
            {"id": d.id, "name": d.name, "code": d.code}
            for d in db.scalars(query.order_by(Department.name))
        ],
        "years": [
            {"id": y.id, "label": y.label, "starts_on": y.starts_on}
            for y in db.scalars(select(AcademicYear).order_by(AcademicYear.starts_on.desc()))
        ],
        "topics": [
            {"id": t.id, "code": t.code, "name": t.name}
            for t in db.scalars(select(Topic).order_by(Topic.name))
        ],
    }


@router.get("/nptel/courses")
def courses(
    db: DB,
    actor: Current,
    request: Request,
    q: str = Query("", max_length=100),
    category: str = Query("", max_length=160),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    query = select(Course)
    if q:
        query = query.where(
            Course.title.icontains(q, autoescape=True) | Course.code.icontains(q, autoescape=True)
        )
    if category:
        query = query.where(
            Course.id.in_(
                select(Offering.course_id)
                .join(ProviderSnapshot, ProviderSnapshot.id == Offering.current_snapshot_id)
                .where(ProviderSnapshot.metadata_json["categories"].contains([category]))
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = []
    for course in db.scalars(query.order_by(Course.title).offset(offset).limit(limit)):
        offerings = [
            offering_view(db, actor, request, o)
            for o in db.scalars(
                select(Offering)
                .where(Offering.course_id == course.id)
                .order_by(Offering.provider_id)
            )
        ]
        items.append(course_view(db, course) | {"offerings": offerings})
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/nptel/courses/{course_id}")
def course_detail(
    course_id: UUID, db: DB, actor: Current, request: Request, department_id: UUID | None = None
) -> dict[str, Any]:
    row = service.get_course(db, course_id)
    return course_view(db, row) | {
        "offerings": [
            offering_view(db, actor, request, o, department_id)
            for o in db.scalars(
                select(Offering)
                .where(Offering.course_id == course_id)
                .order_by(Offering.provider_id)
            )
        ],
        "history": common.history(db, row.id),
    }


@router.get("/nptel/offerings/{offering_id}")
def offering_detail(
    offering_id: UUID, db: DB, actor: Current, request: Request, department_id: UUID | None = None
) -> dict[str, Any]:
    row = db.get(Offering, offering_id)
    if not row:
        raise HTTPException(404, "OFFERING_NOT_FOUND")
    observations = [
        {
            "id": s.id,
            "digest": s.digest,
            "source_url": s.source_url,
            "trust": s.trust,
            "observed_at": s.observed_at,
            "metadata": s.metadata_json,
        }
        for s in db.scalars(
            select(ProviderSnapshot)
            .where(ProviderSnapshot.offering_id == row.id)
            .order_by(ProviderSnapshot.observed_at.desc())
            .limit(30)
        )
    ]
    fetches = [
        {"status": f.status, "error": f.error_code, "observed_at": f.observed_at}
        for f in db.scalars(
            select(ProviderFetch)
            .where(ProviderFetch.offering_id == row.id)
            .order_by(ProviderFetch.observed_at.desc())
            .limit(20)
        )
    ]
    return offering_view(db, actor, request, row, department_id) | {
        "course": course_view(db, service.get_course(db, row.course_id)),
        "observations": observations,
        "fetches": fetches,
        "history": common.history(db, row.id),
    }


@router.post("/admin/nptel/courses", response_model=CommandResult)
def course_write(
    body: CourseWrite, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_course(db, actor, idempotency_key, body)


@router.post("/admin/nptel/provider-fetches", response_model=CommandResult)
def fetch_offering(
    body: OfferingFetch, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    require_admin(actor)
    service.get_course(db, body.course_id)
    db.commit()  # NO provider HTTP during a database transaction.
    observation, error = None, None
    try:
        observation = provider.fetch(body.provider_id)
    except provider.ProviderError as exc:
        error = str(exc)
    return service.record_fetch(db, actor, idempotency_key, body, observation, error)


@router.post("/admin/nptel/local-fixtures", response_model=CommandResult)
def local_offering(
    body: DemoOffering, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    if not request.app.state.settings.demo_enabled or actor.demo is None:
        raise HTTPException(404, "NOT_FOUND")
    return service.record_fetch(db, actor, idempotency_key, body, service.local_observation(body))


@router.post("/admin/nptel/offerings/{offering_id}/accept", response_model=CommandResult)
def accept(
    offering_id: UUID,
    body: SnapshotAccept,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return service.accept_snapshot(
        db, actor, idempotency_key, offering_id, body, request.app.state.settings
    )


@router.get("/nptel/topics")
def topics(db: DB, actor: Current) -> dict[str, Any]:
    return {
        "items": [
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "version": t.version,
                "source_reference": t.source_reference,
                "aliases": [
                    {"label": a.label, "source_reference": a.source_reference}
                    for a in db.scalars(select(TopicAlias).where(TopicAlias.topic_id == t.id))
                ],
                "history": common.history(db, t.id),
            }
            for t in db.scalars(select(Topic).order_by(Topic.name))
        ]
    }


@router.post("/admin/nptel/topics", response_model=CommandResult)
def topic_write(
    body: TopicWrite, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_topic(db, actor, idempotency_key, body)


@router.post("/admin/nptel/topic-aliases", response_model=CommandResult)
def alias_write(
    body: AliasWrite, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_alias(db, actor, idempotency_key, body)


@router.get("/nptel/topic-proposals")
def proposals(db: DB, actor: Current) -> dict[str, Any]:
    query = select(TopicProposal)
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        query = query.where(
            TopicProposal.department_id.in_(set(actor.scopes) | {actor.department.id})
        )
    return {
        "items": [
            {
                "id": p.id,
                "department_id": p.department_id,
                "label": p.normalized_label,
                "source_reference": p.source_reference,
                "reason": p.reason,
                "status": p.status,
                "topic_id": p.topic_id,
            }
            for p in db.scalars(query.order_by(TopicProposal.created_at.desc()).limit(100))
        ]
    }


@router.post("/nptel/topic-proposals", response_model=CommandResult)
def proposal_write(
    body: ProposalWrite, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.propose_topic(db, actor, idempotency_key, body)


@router.post("/admin/nptel/topic-proposals/{proposal_id}/resolve", response_model=CommandResult)
def proposal_resolve(
    proposal_id: UUID,
    body: ProposalResolve,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return service.resolve_proposal(db, actor, idempotency_key, proposal_id, body)


@router.post("/nptel/mapping-requests", response_model=CommandResult)
def mapping_request(
    body: MappingIntake, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.request_mapping(db, actor, idempotency_key, body)


@router.get("/departments/{department_id}/topic-mappings")
def mappings(department_id: UUID, db: DB, actor: Current) -> dict[str, Any]:
    common.department_scope(actor, department_id)
    courses = list(db.scalars(select(Course).order_by(Course.title).limit(200)))
    items = []
    for c in courses:
        mapping = service.current_mapping(db, department_id, c.id)
        pending = (
            db.scalar(
                select(func.count())
                .select_from(MappingRequest)
                .where(
                    MappingRequest.department_id == department_id,
                    MappingRequest.course_id == c.id,
                    MappingRequest.status == "REVIEW_PENDING",
                )
            )
            or 0
        )
        items.append(
            course_view(db, c)
            | {
                "mapping_id": mapping.mapping_id if mapping else None,
                "topic_id": mapping.topic_id if mapping else None,
                "topic": (
                    db.scalar(select(Topic.name).where(Topic.id == mapping.topic_id))
                    or "Unavailable"
                )
                if mapping
                else None,
                "mapping_version": mapping.version if mapping else 0,
                "status": "REVIEW_PENDING" if pending else "APPROVED" if mapping else "UNMAPPED",
                "pending_requests": pending,
            }
        )
    return {"items": items}


@router.get("/departments/{department_id}/topic-mappings/{course_id}")
def mapping_detail(
    department_id: UUID, course_id: UUID, db: DB, actor: Current, request: Request
) -> dict[str, Any]:
    common.department_scope(actor, department_id)
    anchor = db.scalar(
        select(MappingAnchor).where(
            MappingAnchor.department_id == department_id, MappingAnchor.course_id == course_id
        )
    )
    revisions = (
        [
            {
                "id": r.id,
                "version": r.version,
                "topic_id": r.topic_id,
                "topic": (
                    db.scalar(select(Topic.name).where(Topic.id == r.topic_id)) or "Unavailable"
                ),
                "snapshot_id": r.snapshot_id,
                "actor_id": r.actor_id,
                "office_id": r.office_id,
                "valid_from": r.valid_from,
                "valid_until": r.valid_until,
                "reason": r.reason,
                "source_reference": r.source_reference,
            }
            for r in db.scalars(
                select(MappingRevision)
                .where(MappingRevision.mapping_id == anchor.id)
                .order_by(MappingRevision.version.desc())
            )
        ]
        if anchor
        else []
    )
    offerings = list(db.scalars(select(Offering).where(Offering.course_id == course_id)))
    candidates = []
    for offering in offerings:
        s = service.snapshot(db, offering)
        if s:
            candidates.append(
                {
                    "snapshot_id": s.id,
                    "provider_id": offering.provider_id,
                    "categories": s.metadata_json["categories"],
                    "topic_ids": service.topic_candidates(db, s),
                    "observed_at": s.observed_at,
                    "source_url": s.source_url,
                }
            )
    return {
        "course": course_view(db, service.get_course(db, course_id)),
        "department_id": department_id,
        "version": anchor.version if anchor else 0,
        "revisions": revisions,
        "candidates": candidates,
        "history": common.history(db, anchor.id) if anchor else [],
        "existing_allocation_policy": "POLICY_PENDING:P-NEW-11",
    }


@router.post(
    "/departments/{department_id}/topic-mappings/{course_id}", response_model=CommandResult
)
def mapping_write(
    department_id: UUID,
    course_id: UUID,
    body: MappingWrite,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return service.write_mapping(
        db, actor, idempotency_key, department_id, course_id, body, request.app.state.settings
    )


@router.get("/departments/{department_id}/quotas")
def quotas(
    department_id: UUID, db: DB, actor: Current, academic_year_id: UUID | None = None
) -> dict[str, Any]:
    common.department_scope(actor, department_id)
    query = select(QuotaPool).where(QuotaPool.department_id == department_id)
    if academic_year_id:
        query = query.where(QuotaPool.academic_year_id == academic_year_id)
    return {
        "items": [pool_view(db, p) for p in db.scalars(query.order_by(QuotaPool.id).limit(200))]
    }


@router.post("/departments/{department_id}/quotas", response_model=CommandResult)
def quota_write(
    department_id: UUID,
    body: QuotaWrite,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return write_pool(db, actor, idempotency_key, department_id, body)


@router.get("/quotas/{pool_id}")
def quota_detail(
    pool_id: UUID, db: DB, actor: Current, as_of: datetime | None = None
) -> dict[str, Any]:
    row = db.get(QuotaPool, pool_id)
    if not row:
        raise HTTPException(404, "POOL_NOT_FOUND")
    common.department_scope(actor, row.department_id)
    from akus.applications.router import quota_history

    return pool_view(db, row) | quota_history(db, actor, row, as_of)
