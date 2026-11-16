from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from sqlalchemy import select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.auth import csrf_valid
from akus.people import service
from akus.people.models import Department
from akus.people.schemas import (
    AppointmentCreate,
    AppointmentEnd,
    AppointmentPage,
    AppointmentView,
    CommandResult,
    DepartmentView,
    StaffCreate,
    StaffDetail,
    StaffPage,
)

router = APIRouter(prefix="/api/v1", tags=["People and access"])


def mutation_guard(request: Request, actor: Current) -> None:
    if request.headers.get("origin") != request.app.state.settings.public_origin:
        raise HTTPException(403, "ORIGIN_REJECTED")
    if not csrf_valid(actor.session, request.headers.get("x-csrf-token", "")):
        raise HTTPException(403, "CSRF_REJECTED")
    service.require_admin(actor)


@router.get("/people/departments", response_model=list[DepartmentView])
def departments(db: DB, actor: Current) -> list[DepartmentView]:
    query = select(Department)
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        query = query.where(Department.id.in_([actor.department.id, *actor.scopes]))
    return [DepartmentView.model_validate(d) for d in db.scalars(query.order_by(Department.code))]


@router.get("/people/staff", response_model=StaffPage)
def staff(
    db: DB,
    actor: Current,
    q: str = Query("", max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> StaffPage:
    return service.list_staff(db, actor, q, offset, limit)


@router.get("/people/staff/{person_id}", response_model=StaffDetail)
def staff_detail(person_id: UUID, db: DB, actor: Current) -> StaffDetail:
    return service.detail(db, actor, person_id)


@router.get("/me/authority", response_model=StaffDetail)
def own_authority(db: DB, actor: Current) -> StaffDetail:
    return service.detail(db, actor, actor.person.id)


@router.post("/admin/staff", response_model=CommandResult, status_code=201)
def add_staff(
    body: StaffCreate,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.create_staff(db, actor, idempotency_key, body)


@router.get("/people/appointments", response_model=AppointmentPage)
def appointments(
    db: DB, actor: Current, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)
) -> AppointmentPage:
    return service.list_appointments(db, actor, offset, limit)


@router.post("/admin/appointments", response_model=CommandResult, status_code=201)
def add_appointment(
    body: AppointmentCreate,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.create_appointment(db, actor, idempotency_key, body)


@router.post("/admin/appointments/{appointment_id}/end", response_model=CommandResult)
def end_appointment(
    appointment_id: UUID,
    body: AppointmentEnd,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    return service.end_appointment(db, actor, idempotency_key, appointment_id, body)


@router.get("/people/appointments/{appointment_id}", response_model=AppointmentView)
def appointment_detail(appointment_id: UUID, db: DB, actor: Current) -> AppointmentView:
    return service.appointment_detail(db, actor, appointment_id)
