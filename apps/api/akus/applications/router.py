from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.applications import service, transfers
from akus.applications.models import (
    AcademicNotice,
    Allocation,
    Application,
    Ledger,
    Reconciliation,
    Submission,
)
from akus.applications.schemas import (
    DraftWrite,
    Recheck,
    Review,
    ScheduleClaim,
    Submit,
    VerifySchedule,
    Withdraw,
)
from akus.catalog import common
from akus.catalog.models import Course, Offering
from akus.catalog.router import Key, mutation_guard, offering_view
from akus.catalog.service import snapshot
from akus.people.models import Person
from akus.people.schemas import CommandResult
from akus.quotas.models import QuotaPool
from akus.quotas.service import pool_view

router = APIRouter(prefix="/api/v1", tags=["Applications and quota reconciliation"])


def ledger_view(row: Ledger) -> dict[str, Any]:
    return {
        "id": row.id,
        "movement_id": row.movement_id,
        "application_id": row.application_id,
        "pool_id": row.pool_id,
        "delta": row.delta,
        "kind": row.kind,
        "snapshot_id": row.snapshot_id,
        "personal_schedule_id": row.personal_schedule_id,
        "recorded_at": row.recorded_at,
    }


def app_view(
    db: DB, actor: Current, request: Request, app: Application, detail: bool = False
) -> dict[str, Any]:
    course, offering, person = (
        db.get(Course, app.course_id),
        db.get(Offering, app.offering_id),
        db.get(Person, app.person_id),
    )
    allocation, submitted = db.get(Allocation, app.id), db.get(Submission, app.id)
    cases = list(
        db.scalars(
            select(Reconciliation)
            .where(Reconciliation.application_id == app.id)
            .order_by(Reconciliation.updated_at.desc())
        )
    )
    pool = db.get(QuotaPool, allocation.pool_id) if allocation else None
    can_review = (
        app.state == "UNDER_REVIEW"
        and app.person_id != actor.person.id
        and any(
            o.department_id == app.department_id
            and (
                o.office == app.next_office or app.next_office == "HOD" and o.office == "ACTING_HOD"
            )
            for o in actor.offices
        )
    )
    from akus.applications.personal_schedule import current as current_personal_schedule

    personal = current_personal_schedule(db, app.id)
    original_cutoff = submitted.facts["metadata"].get("enrollment_ends_on") if submitted else None
    current_source = snapshot(db, offering) if offering and app.state == "UNDER_REVIEW" else None
    current_cutoff = (
        current_source.metadata_json.get("enrollment_ends_on") if current_source else None
    )
    result: dict[str, Any] = {
        "enrollment_deadline_passed": app.state == "UNDER_REVIEW"
        and any(
            day and service.today() > date.fromisoformat(day)
            for day in (original_cutoff, current_cutoff)
        ),
        "id": app.id,
        "person_id": app.person_id,
        "applicant": person.display_name if person else None,
        "course": course.title if course else None,
        "course_id": app.course_id,
        "offering_id": app.offering_id,
        "provider_id": offering.provider_id if offering else None,
        "department_id": app.department_id,
        "state": app.state,
        "version": app.version,
        "next_office": app.next_office,
        "submitted_at": app.submitted_at,
        "can_review": can_review,
        "own": app.person_id == actor.person.id,
        "allocation": {
            "state": allocation.state,
            "version": allocation.version,
            "pool": pool_view(db, pool),
        }
        if allocation and pool
        else None,
        "source_eligible": service.applicant_still_eligible(db, app),
        "personal_schedule": {
            "id": personal.id,
            "version": personal.version,
            "scheduled_exam_on": personal.scheduled_exam_on,
            "source_reference": personal.source_reference,
            "document_digest": personal.document_digest,
            "observed_at": personal.observed_at,
            "verified_at": personal.verified_at,
            "verification": "MANUAL_HOD_AUTHENTICATED",
        }
        if personal
        else None,
        "cases": [
            {
                "id": c.id,
                "kind": c.kind,
                "status": c.status,
                "reason": c.reason,
                "context": c.context,
                "updated_at": c.updated_at,
            }
            for c in cases
        ],
    }
    if detail:
        from akus.applications import participation
        from akus.applications.workflow_models import DraftRevision
        from akus.exceptions.history import report

        historical = report(db, app, datetime.now(UTC)) if app.state == "SEPARATED" else {}
        finding = historical.get("finding")
        from akus.compliance.credentials import certified
        from akus.compliance.models import CredentialEvent

        actual = certified(db, app.id)
        if (
            isinstance(actual, CredentialEvent)
            and actual.kind == "VERIFIED"
            and (not finding or actual.recorded_at >= finding["recorded_at"])
        ):
            from akus.compliance.assessment import assess
            from akus.people.models import EmploymentEpisode

            ep = db.get_one(EmploymentEpisode, app.episode_id)
            annual = assess(db, ep)["annual"]
            historical = {"annual": {y["year"]: y["status"] for y in annual}}
            finding = actual.facts
        suspended = any(c.kind == "INTEGRITY" and c.status == "OPEN" for c in cases)
        result |= {
            "participation": participation.view(db, app),
            "draft_revisions": [
                {"version": r.version, "recorded_at": r.recorded_at, "declarations": r.declarations}
                for r in db.scalars(
                    select(DraftRevision)
                    .where(DraftRevision.application_id == app.id)
                    .order_by(DraftRevision.version.desc())
                )
            ],
            "declarations": app.declarations,
            "offering": offering_view(
                db, actor, request, offering, app.department_id, authorized_history=True
            )
            if offering
            else None,
            "submission": {
                "facts": submitted.facts,
                "original_pool_id": submitted.original_pool_id,
                "submitted_at": submitted.submitted_at,
            }
            if submitted
            else None,
            "history": common.history(db, app.id),
            "ledger": [
                ledger_view(entry)
                for entry in db.scalars(
                    select(Ledger)
                    .where(Ledger.application_id == app.id)
                    .order_by(Ledger.recorded_at)
                )
            ],
            "notifications": [
                {"kind": n.kind, "facts": n.facts, "created_at": n.created_at}
                for n in db.scalars(
                    select(AcademicNotice)
                    .where(AcademicNotice.application_id == app.id)
                    .order_by(AcademicNotice.created_at.desc())
                    .limit(100)
                )
            ],
            "actual_exam": finding["actual_exam_on"] if finding else "NOT_VERIFIED",
            "annual_compliance": "SUSPENDED"
            if suspended
            else "INELIGIBLE"
            if app.state == "INVALIDATED"
            else historical.get("annual", {}).get(finding["academic_year"], "NOT_ASSESSED")
            if finding
            else "NOT_ASSESSED",
        }
    return result


@router.get("/applications")
def listing(
    db: DB,
    actor: Current,
    request: Request,
    review: bool = False,
    reconciliation: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    query = service.scoped_query(actor)
    if review:
        query = query.where(
            Application.state == "UNDER_REVIEW", Application.person_id != actor.person.id
        )
    if reconciliation:
        query = query.where(
            Application.id.in_(
                select(Reconciliation.application_id).where(Reconciliation.status == "OPEN")
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    return {
        "items": [
            app_view(db, actor, request, a)
            for a in db.scalars(
                query.order_by(Application.created_at.desc()).offset(offset).limit(limit)
            )
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/quota-transfer-cases/{case_id}")
def case_detail(case_id: UUID, db: DB, actor: Current, request: Request) -> dict[str, Any]:
    if not set(actor.roles) & {"HOD", "PRINCIPAL"}:
        raise HTTPException(403, "QUOTA_CASE_OVERSIGHT_REQUIRED")
    case = db.get(Reconciliation, case_id)
    if not case:
        raise HTTPException(404, "QUOTA_CASE_NOT_FOUND")
    app = db.get(Application, case.application_id)
    assert app
    service.can_read(actor, app)
    return app_view(db, actor, request, app, True)


@router.get("/applications/{app_id}")
def detail(app_id: UUID, db: DB, actor: Current, request: Request) -> dict[str, Any]:
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(404, "APPLICATION_NOT_FOUND")
    service.can_read(actor, app)
    return app_view(db, actor, request, app, True)


@router.post("/applications", response_model=CommandResult)
def save(
    body: DraftWrite, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.draft(db, actor, idempotency_key, body)


@router.post("/applications/{app_id}/submit", response_model=CommandResult)
def submit(
    app_id: UUID, body: Submit, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.submit(db, actor, idempotency_key, app_id, body, request.app.state.settings)


@router.post("/applications/{app_id}/review", response_model=CommandResult)
def review(
    app_id: UUID, body: Review, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.review(db, actor, idempotency_key, app_id, body, request.app.state.settings)


@router.post("/applications/{app_id}/withdraw", response_model=CommandResult)
def withdraw(
    app_id: UUID, body: Withdraw, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return service.withdraw(db, actor, idempotency_key, app_id, body, request.app.state.settings)


@router.post("/applications/{app_id}/reconcile", response_model=CommandResult)
def reconcile(
    app_id: UUID, body: Recheck, request: Request, db: DB, actor: Current, idempotency_key: Key
) -> CommandResult:
    mutation_guard(request, actor)
    return transfers.manual(db, actor, idempotency_key, app_id, body)


def quota_history(
    db: DB, actor: Current, pool: QuotaPool, as_of: datetime | None = None
) -> dict[str, Any]:
    # Aggregate capacity is visible to department faculty; other people's records are not.
    privileged = (
        bool(set(actor.roles) & {"ADMIN", "PRINCIPAL"}) or pool.department_id in actor.scopes
    )
    apps = (
        select(Application, Allocation, Person)
        .join(Allocation, Allocation.application_id == Application.id)
        .join(Person, Person.id == Application.person_id)
        .where(Allocation.pool_id == pool.id)
    )
    ledger = select(Ledger).where(Ledger.pool_id == pool.id)
    if not privileged:
        apps = apps.where(Application.person_id == actor.person.id)
        ledger = ledger.where(
            Ledger.application_id.in_(
                select(Application.id).where(Application.person_id == actor.person.id)
            )
        )
    balance_query = select(func.coalesce(func.sum(Ledger.delta), 0)).where(
        Ledger.pool_id == pool.id
    )
    if as_of:
        if as_of.tzinfo is None:
            raise HTTPException(422, "AS_OF_TIMEZONE_REQUIRED")
        ledger = ledger.where(Ledger.recorded_at <= as_of)
        balance_query = balance_query.where(Ledger.recorded_at <= as_of)
    actual = (
        db.scalar(
            select(func.count())
            .select_from(Allocation)
            .where(Allocation.pool_id == pool.id, Allocation.state != "RELEASED")
        )
        or 0
    )
    return {
        "allocations": [
            {
                "application_id": a.id,
                "applicant": person.display_name,
                "state": a.state,
                "allocation_state": allocation.state,
            }
            for a, allocation, person in db.execute(
                apps.order_by(Application.created_at).limit(200)
            )
        ],
        "ledger": [
            ledger_view(entry)
            for entry in db.scalars(ledger.order_by(Ledger.recorded_at.desc()).limit(200))
        ],
        "reconciliation": {
            "stored_count": pool.occupied,
            "counted_allocations": actual,
            "ledger_balance": db.scalar(balance_query),
            "as_of": as_of,
            "matches_current": None
            if as_of
            else actual == pool.occupied and db.scalar(balance_query) == pool.occupied,
        },
        "history": common.history(db, pool.id),
        "visibility": "DEPARTMENT" if privileged else "OWN_ALLOCATIONS_ONLY",
        "row_limit": 200,
    }


@router.post("/applications/{app_id}/schedule-claims", response_model=CommandResult)
def schedule_claim(
    app_id: UUID,
    body: ScheduleClaim,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor, idempotency_key)
    app, offering = service.lock_application(db, app_id, actor)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "OWN_APPLICATION_REQUIRED")
    op = f"PERSON_SCHEDULE_REPORTED:{app_id}"
    if result := common.replay(db, actor, idempotency_key, op, body):
        return result
    if app.state not in {"UNDER_REVIEW", "APPROVED"}:
        raise HTTPException(409, "ACTIVE_APPLICATION_REQUIRED")
    data = body.model_dump(mode="json") | {
        "person_id": str(app.person_id),
        "offering_id": str(offering.id),
        "trust": "UNVERIFIED_ASSERTION",
        "verification": "HOD_VERIFICATION_PENDING",
    }
    service.case(db, app, "PERSON_SCHEDULE", "HOD_VERIFICATION_PENDING", data)
    return common.finish(db, actor, idempotency_key, op, body, app.id, data, app.department_id)


@router.post("/applications/{app_id}/verify-schedule", response_model=CommandResult)
def verify_schedule(
    app_id: UUID,
    body: VerifySchedule,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    from akus.applications.personal_schedule import verify

    return verify(db, actor, idempotency_key, app_id, body)


from akus.applications import participation  # noqa: E402
from akus.applications.participation_schemas import (  # noqa: E402
    DecideWithdrawal,
    EnrollmentProof,
    EnrollmentVerify,
    RequestWithdrawal,
)


@router.post("/applications/{app_id}/enrollment-claims", response_model=CommandResult)
def enrollment_claim(
    app_id: UUID,
    body: EnrollmentProof,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return participation.claim(db, actor, idempotency_key, app_id, body)


@router.post("/applications/{app_id}/verify-enrollment", response_model=CommandResult)
def verify_enrollment(
    app_id: UUID,
    body: EnrollmentVerify,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return participation.verify(db, actor, idempotency_key, app_id, body)


@router.post("/applications/{app_id}/withdrawal-requests", response_model=CommandResult)
def request_withdrawal(
    app_id: UUID,
    body: RequestWithdrawal,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return participation.request_withdrawal(
        db, actor, idempotency_key, app_id, body, request.app.state.settings
    )


@router.post("/applications/{app_id}/withdrawal-decision", response_model=CommandResult)
def decide_withdrawal(
    app_id: UUID,
    body: DecideWithdrawal,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Key,
) -> CommandResult:
    mutation_guard(request, actor)
    return participation.decide_withdrawal(
        db, actor, idempotency_key, app_id, body, request.app.state.settings
    )
