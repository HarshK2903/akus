"""Workspace registers, personal inbox and auditable operational commands."""

import csv
from datetime import datetime
from io import StringIO
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.catalog import common
from akus.catalog.router import Key, mutation_guard
from akus.compliance.router import report_reader
from akus.models import AuditEvent, WorkerHeartbeat, WorkJob
from akus.people.schemas import CommandResult
from akus.workspace import personal, registers
from akus.workspace.models import NoticePreference, NoticeRead, NoticeTemplate, PersonalNotice

router = APIRouter(prefix="/api/v1", tags=["Workspace"])


class Filters(BaseModel):
    search: str = Field(default="", max_length=160)
    status: str = Field(default="", max_length=60)
    department: UUID | None = None
    year: UUID | None = None
    topic: UUID | None = None
    since: datetime | None = None
    until: datetime | None = None


@router.get("/registers/{report}")
def register(
    report: str,
    db: DB,
    actor: Current,
    filters: Annotated[Filters, Depends()],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, Any]:
    actor = report_reader(db, actor)
    if report == "notifications":
        preference = db.get(NoticePreference, actor.person.id)
        initial = preference.initial_filter if preference else "ALL"
        status = initial if filters.status in {"", "DEFAULT"} else filters.status
        filters.status = "" if status == "ALL" else status
    result = registers.fetch(db, actor, report, offset=offset, limit=limit, **filters.model_dump())
    if report == "notifications":
        result["initial_filter"] = initial
    return result


@router.post("/registers/{report}/export")
def export(report: str, filters: Filters, request: Request, actor: Current, db: DB) -> Response:
    mutation_guard(request, actor)
    if report not in {
        "department-applications",
        "drc-history",
        "hod-history",
        "departments",
        "applications",
        "topics-quotas",
        "exceptions",
        "audit",
        "source-audit",
    }:
        raise HTTPException(404, "EXPORT_UNAVAILABLE")
    db.rollback()
    db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
    actor = common.refresh(db, actor)
    result = registers.fetch(db, actor, report, limit=5000, **filters.model_dump())
    if result["total"] > 5000:
        raise HTTPException(422, "NARROW_EXPORT_FILTERS")
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    columns = ["id", "title", "context", "status", "recorded_at"]
    writer.writerow(columns)
    for row in result["items"]:
        values = [str(row[c]) if row[c] is not None else "" for c in columns]
        writer.writerow(
            [
                "'" + v
                if v.lstrip().startswith(("=", "+", "-", "@")) or v.startswith(("\r", "\n", "\t"))
                else v
                for v in values
            ]
        )
    db.add(
        AuditEvent(
            actor_id=actor.demo.id if actor.demo else None,
            action="REGISTER_EXPORTED",
            details={
                "actor_person_id": str(actor.person.id),
                "register": report,
                "count": str(result["total"]),
                "filters": filters.model_dump_json(exclude_defaults=True),
            },
        )
    )
    db.commit()
    return Response(
        stream.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="akus-{report}.csv"',
            "Cache-Control": "no-store",
        },
    )


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Preference(Command):
    initial_filter: Literal["ALL", "UNREAD"]


class TemplateEdit(Command):
    expected_version: int = Field(ge=0)
    heading: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class Retry(Command):
    expected_attempts: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


@router.post("/notifications/preference")
def preference(body: Preference, request: Request, actor: Current, db: DB) -> dict[str, str]:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor)
    db.execute(
        insert(NoticePreference)
        .values(person_id=actor.person.id, initial_filter=body.initial_filter)
        .on_conflict_do_update(
            index_elements=["person_id"], set_={"initial_filter": body.initial_filter}
        )
    )
    db.commit()
    return {"initial_filter": body.initial_filter}


@router.post("/notifications/{notice_id}/read")
def mark_read(notice_id: UUID, request: Request, actor: Current, db: DB) -> dict[str, str]:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor)
    if not db.scalar(
        text("SELECT EXISTS(SELECT 1 FROM (" + personal.NOTICES + ") n WHERE n.id=:id)"),
        {"person": actor.person.id, "id": notice_id},
    ):
        raise HTTPException(404, "NOTICE_NOT_FOUND")
    db.execute(
        insert(NoticeRead)
        .values(person_id=actor.person.id, notice_id=notice_id)
        .on_conflict_do_nothing()
    )
    db.commit()
    return {"status": "READ"}


@router.get("/admin/notification-settings")
def templates(db: DB, actor: Current) -> dict[str, Any]:
    registers.allowed(report_reader(db, actor), "ADMIN")
    versions = db.scalars(
        select(NoticeTemplate).order_by(NoticeTemplate.version.desc()).limit(50)
    ).all()
    return {
        "category": "APPLICATION",
        "default_heading": "Application update",
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "heading": v.heading,
                "reason": v.reason,
                "actor_id": v.actor_id,
                "recorded_at": v.recorded_at,
            }
            for v in versions
        ],
    }


@router.post("/admin/notification-settings")
def change_template(
    body: TemplateEdit, key: Key, request: Request, db: DB, actor: Current
) -> CommandResult:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor, key)
    registers.allowed(actor, "ADMIN")
    op = "NOTIFICATION_TEMPLATE_CHANGED"
    replay = common.replay(db, actor, key, op, body)
    if replay:
        return replay
    db.execute(text("SELECT pg_advisory_xact_lock(8210801)"))
    current = db.scalar(select(func.max(NoticeTemplate.version))) or 0
    if body.expected_version != current:
        raise HTTPException(409, "TEMPLATE_VERSION_CHANGED")
    row = NoticeTemplate(
        category="APPLICATION",
        version=current + 1,
        heading=body.heading,
        reason=body.reason,
        actor_id=actor.person.id,
    )
    db.add(row)
    db.flush()
    return common.finish(db, actor, key, op, body, row.id, body.model_dump())


@router.post("/admin/notification-settings/test")
def test_notice(body: Command, key: Key, request: Request, db: DB, actor: Current) -> CommandResult:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor, key)
    registers.allowed(actor, "ADMIN")
    op = "NOTIFICATION_TEST_SENT"
    replay = common.replay(db, actor, key, op, body)
    if replay:
        return replay
    heading = (
        db.scalar(select(NoticeTemplate.heading).order_by(NoticeTemplate.version.desc()).limit(1))
        or "Application update"
    )
    notice = PersonalNotice(person_id=actor.person.id, category="APPLICATION", heading=heading)
    db.add(notice)
    db.flush()
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        notice.id,
        {"channel": "IN_APP", "recipient": str(actor.person.id)},
    )


@router.get("/admin/worker-health")
def worker_health(db: DB, actor: Current) -> dict[str, Any]:
    registers.allowed(report_reader(db, actor), "ADMIN")
    return {
        "seen_at": db.scalar(
            select(WorkerHeartbeat.seen_at).where(WorkerHeartbeat.name == "foundation")
        )
    }


@router.post("/admin/work/{job_id}/retry")
def retry(
    job_id: UUID, body: Retry, key: Key, request: Request, db: DB, actor: Current
) -> CommandResult:
    mutation_guard(request, actor)
    actor = common.refresh(db, actor, key)
    registers.allowed(actor, "ADMIN")
    op = f"WORK_RETRIED:{job_id}"
    replay = common.replay(db, actor, key, op, body)
    if replay:
        return replay
    job = db.scalar(select(WorkJob).where(WorkJob.id == job_id).with_for_update())
    if not job:
        raise HTTPException(404, "WORK_NOT_FOUND")
    if (
        job.state != "DEAD"
        or job.kind not in {"QUOTA_RECHECK", "PROVIDER_REFRESH", "OFFICE_INBOX"}
        or job.attempts != body.expected_attempts
    ):
        raise HTTPException(409, "WORK_NOT_RETRYABLE")
    job.state = "PENDING"
    job.next_attempt_at = None
    return common.finish(db, actor, key, op, body, job.id, body.model_dump())


@router.get("/dashboard/academic")
def academic_summary(db: DB, actor: Current) -> dict[str, Any]:
    from akus.applications.service import today
    from akus.compliance import assessment

    actor = report_reader(db, actor)
    metrics: list[dict[str, Any]] = []
    if actor.view().applicant_eligible:
        report = assessment.assess(db, actor.episode)
        year = next(
            (y for y in report["annual"] if y["starts_on"] <= str(today()) <= y["ends_on"]),
            None,
        )
        metrics.extend(
            [
                {
                    "label": "This academic year",
                    "value": year["status"] if year else "YEAR_NOT_CONFIGURED",
                    "href": "/app/compliance/annual",
                },
                {
                    "label": "Subject-wise Silver records",
                    "value": len(report["silver"]),
                    "href": "/app/compliance/silver",
                },
            ]
        )
    total = db.scalar(
        text("SELECT count(*) FROM (" + personal.tasks(actor) + ") t"),
        {"person": actor.person.id, "episode": actor.episode.id, "scopes": actor.scopes},
    )
    metrics.append({"label": "Open tasks in scope", "value": total, "href": "/app/tasks"})
    if "PRINCIPAL" in actor.roles or "HOD" in actor.roles:
        scope = (
            ""
            if "PRINCIPAL" in actor.roles
            else " WHERE department_id=ANY(CAST(:scopes AS uuid[]))"
        )
        count = db.scalar(
            text("SELECT coalesce(sum(occupied),0) FROM department_topic_quotas" + scope),
            {"scopes": actor.scopes},
        )
        metrics.append(
            {
                "label": "Counted seats across published pools",
                "value": count,
                "href": "/principal/topics-quotas" if "PRINCIPAL" in actor.roles else "/hod/quotas",
            }
        )
    if "ADMIN" in actor.roles:
        metrics.append(
            {
                "label": "Jobs awaiting operational review",
                "value": db.scalar(
                    select(func.count()).select_from(WorkJob).where(WorkJob.state == "DEAD")
                ),
                "href": "/admin/operations?status=DEAD",
            }
        )
    return {"metrics": metrics}
