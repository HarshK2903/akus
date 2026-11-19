from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, or_, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.applications import outcomes, service
from akus.applications.outcome_models import Attempt
from akus.applications.outcome_schemas import AttemptWrite, OutcomeDecision
from akus.catalog.models import Course, Offering
from akus.catalog.router import Key, mutation_guard
from akus.people.models import DepartmentAssignment, EmploymentEpisode, Person
from akus.people.schemas import CommandResult

router = APIRouter(prefix="/api/v1", tags=["Prior attempts and independent outcome verification"])


@router.get("/previous-attempts")
@router.get("/outcome-verifications")
def listing(
    db: DB,
    actor: Current,
    request: Request,
    search: str = Query("", max_length=200),
    order: Literal["newest", "oldest"] = "newest",
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    query = select(Attempt)
    if request.url.path.endswith("/previous-attempts"):
        query = query.where(Attempt.person_id == actor.person.id)
    else:
        departments = [o.department_id for o in actor.offices if o.office in {"HOD", "ACTING_HOD"}]
        if not departments:
            raise HTTPException(403, "CURRENT_DEPARTMENT_HOD_REQUIRED")
        day = service.today()
        persons = (
            select(EmploymentEpisode.person_id)
            .join(DepartmentAssignment)
            .where(
                DepartmentAssignment.department_id.in_(departments),
                EmploymentEpisode.starts_on <= day,
                or_(EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > day),
                DepartmentAssignment.starts_on <= day,
                or_(
                    DepartmentAssignment.ends_before.is_(None),
                    DepartmentAssignment.ends_before > day,
                ),
            )
        )
        query = query.where(Attempt.person_id.in_(persons))
    if search.strip():
        term = search.strip()
        query = (
            query.join(Course, Attempt.course_id == Course.id)
            .join(Offering, Attempt.offering_id == Offering.id)
            .join(Person, Attempt.person_id == Person.id)
            .where(
                or_(
                    Course.title.icontains(term, autoescape=True),
                    Offering.provider_id.icontains(term, autoescape=True),
                    Person.display_name.icontains(term, autoescape=True),
                )
            )
        )
    sort_key = Attempt.created_at.desc() if order == "newest" else Attempt.created_at.asc()
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    return {
        "items": [
            outcomes.view(db, actor, a, detail=False)
            for a in db.scalars(query.order_by(sort_key, Attempt.id).offset(offset).limit(limit))
        ],
        "total": count,
    }


@router.get("/previous-attempts/{attempt_id}")
@router.get("/outcome-verifications/{attempt_id}")
def detail(attempt_id: UUID, db: DB, actor: Current) -> dict[str, Any]:
    attempt = db.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "ATTEMPT_NOT_FOUND")
    return outcomes.view(db, actor, attempt)


@router.post("/outcome-verifications", response_model=CommandResult)
def record(body: AttemptWrite, key: Key, db: DB, actor: Current, request: Request) -> CommandResult:
    mutation_guard(request, actor)
    return outcomes.write(db, actor, key, body)


@router.post("/outcome-verifications/{attempt_id}/decision", response_model=CommandResult)
def decide(
    attempt_id: UUID, body: OutcomeDecision, key: Key, db: DB, actor: Current, request: Request
) -> CommandResult:
    mutation_guard(request, actor)
    return outcomes.decide(db, actor, key, attempt_id, body)
