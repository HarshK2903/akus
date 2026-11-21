"""Append-only application attachments and the evidence manifest used at submission."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, Request, Response
from pydantic import Field, field_validator
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from starlette.exceptions import HTTPException

from akus.access import DB, Actor, Current
from akus.applications import service
from akus.applications.models import Application, Submission
from akus.catalog import common
from akus.catalog.router import Key, mutation_guard
from akus.catalog.schemas import Decision
from akus.compliance.documents import ScanResult, inspect_pdf
from akus.compliance.schemas import Attachment
from akus.db import Base
from akus.people.schemas import CommandResult


class EvidenceRevision(Base):
    __tablename__ = "application_attachment_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"))
    series_id: Mapped[UUID]
    version: Mapped[int]
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    kind: Mapped[str] = mapped_column(String(24))
    filename: Mapped[str] = mapped_column(String(140))
    source_reference: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str] = mapped_column(String(2000))
    digest: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int]
    scan: Mapped[str] = mapped_column(String(20))
    content: Mapped[bytes | None] = mapped_column(deferred=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
    __table_args__ = (
        UniqueConstraint(
            "application_id", "series_id", "version", name="one_application_attachment_revision"
        ),
        CheckConstraint(
            "version >= 1 AND size_bytes BETWEEN 1 AND 2097152 AND ((scan IN ('CLEAN','QUARANTINED') AND content IS NOT NULL AND octet_length(content)=size_bytes AND encode(sha256(content),'hex')=digest) OR (scan='REMOVED' AND content IS NULL))",
            name="valid_application_attachment",
        ),
    )


class Change(Decision):
    expected_version: int = Field(ge=1)


class Upload(Change):
    previous_id: UUID | None = None
    kind: Literal["ACADEMIC_RELEVANCE", "ENROLLMENT", "SCHEDULE", "PRIOR_RESULT", "OTHER"]
    filename: str = Field(min_length=1, max_length=140)
    document_digest: str = Field(pattern="^[a-f0-9]{64}$")
    attachment: Attachment

    @field_validator("filename")
    @classmethod
    def filename_only(cls, value: str) -> str:
        if (
            "/" in value
            or "\\" in value
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
            or not value.lower().endswith(".pdf")
        ):
            raise ValueError("A PDF filename without a path is required")
        return value


def manifest(db: Session, aid: UUID) -> list[str]:
    current = (
        select(EvidenceRevision.id, EvidenceRevision.scan)
        .where(EvidenceRevision.application_id == aid)
        .distinct(EvidenceRevision.series_id)
        .order_by(EvidenceRevision.series_id, EvidenceRevision.version.desc())
        .subquery()
    )
    return [
        str(id_)
        for id_ in db.scalars(
            select(current.c.id).where(current.c.scan != "REMOVED").order_by(current.c.id)
        )
    ]


def read_app(db: Session, actor: Actor, aid: UUID) -> Application:
    app = db.get(Application, aid)
    if not app:
        raise HTTPException(404, "APPLICATION_NOT_FOUND")
    if app.person_id != actor.person.id and (
        app.state == "DRAFT"
        or not ("PRINCIPAL" in actor.roles or app.department_id in actor.scopes)
    ):
        raise HTTPException(403, "PRIVATE_APPLICATION_EVIDENCE")
    return app


def owner(actor: Actor, app: Application) -> None:
    common.require_applicant(actor)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "OWN_APPLICATION_REQUIRED")
    service.require_current_episode(actor, app)


router = APIRouter(prefix="/api/v1/applications", tags=["Application evidence"])


@router.get("/{aid}/attachments")
def listing(aid: UUID, db: DB, actor: Current, offset: int = Query(0, ge=0)) -> dict[str, Any]:
    from akus.compliance.router import report_reader

    actor = report_reader(db, actor)
    app = read_app(db, actor, aid)
    ids = set(manifest(db, aid))
    submission = db.get(Submission, aid)
    submitted = set(submission.facts.get("attachment_revision_ids", [])) if submission else set()
    rows = db.scalars(
        select(EvidenceRevision)
        .where(EvidenceRevision.application_id == aid)
        .order_by(EvidenceRevision.recorded_at.desc(), EvidenceRevision.id)
        .offset(offset)
        .limit(25)
    )
    editable = (
        actor.view().applicant_eligible
        and app.person_id == actor.person.id
        and actor.episode.id == app.episode_id
        and app.state in {"DRAFT", "UNDER_REVIEW", "APPROVED"}
    )
    return {
        "total": db.scalar(
            select(func.count())
            .select_from(EvidenceRevision)
            .where(EvidenceRevision.application_id == aid)
        ),
        "can_upload": editable,
        "can_remove": editable and app.state == "DRAFT",
        "application_version": app.version,
        "items": [
            {
                "id": r.id,
                "series_id": r.series_id,
                "version": r.version,
                "kind": r.kind,
                "filename": r.filename,
                "source_reference": r.source_reference,
                "reason": r.reason,
                "digest": r.digest,
                "size_bytes": r.size_bytes,
                "scan": r.scan,
                "recorded_at": r.recorded_at,
                "current": str(r.id) in ids,
                "submitted": str(r.id) in submitted,
                "can_download": app.person_id == actor.person.id and r.scan == "CLEAN",
            }
            for r in rows
        ],
    }


def append(
    db: Session,
    actor: Actor,
    aid: UUID,
    key: UUID,
    body: Change,
    previous: UUID | None,
    pdf: ScanResult | None,
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, _ = service.lock_application(db, aid, actor)
    owner(actor, app)
    op = f"APPLICATION_EVIDENCE_{'UPLOADED' if pdf else 'REMOVED'}:{aid}:{previous or 'NEW'}"
    if replay := common.replay(db, actor, key, op, body):
        return replay
    if app.version != body.expected_version:
        raise HTTPException(409, "VERSION_CONFLICT")
    if app.state not in ({"DRAFT", "UNDER_REVIEW", "APPROVED"} if pdf else {"DRAFT"}):
        raise HTTPException(409, "EVIDENCE_HISTORY_READ_ONLY")
    prior = db.get(EvidenceRevision, previous) if previous else None
    if previous and (
        not prior or prior.application_id != aid or str(previous) not in manifest(db, aid)
    ):
        raise HTTPException(409, "ATTACHMENT_REVISION_CHANGED")
    rid = uuid4()
    kind: str
    if isinstance(body, Upload) and pdf:
        filename, kind, digest, size, scan = (
            body.filename,
            body.kind,
            body.document_digest,
            len(pdf.content),
            pdf.status,
        )
    else:
        assert prior
        filename, kind, digest, size, scan = (
            prior.filename,
            prior.kind,
            prior.digest,
            prior.size_bytes,
            "REMOVED",
        )
    row = EvidenceRevision(
        id=rid,
        series_id=prior.series_id if prior else rid,
        application_id=aid,
        version=prior.version + 1 if prior else 1,
        actor_id=actor.person.id,
        kind=kind,
        filename=filename,
        source_reference=body.source_reference,
        reason=body.reason,
        digest=digest,
        size_bytes=size,
        scan=scan,
        content=pdf.content if pdf else None,
    )
    db.add(row)
    app.version += 1
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        row.id,
        {
            "application_id": str(aid),
            "revision": row.version,
            "digest": digest,
            "scan": scan,
            "scanner_version": pdf.scanner_version if pdf else None,
        },
        app.department_id,
    )


@router.post("/{aid}/attachments")
def upload(
    aid: UUID, body: Upload, request: Request, key: Key, db: DB, actor: Current
) -> CommandResult:
    mutation_guard(request, actor)
    app = read_app(db, actor, aid)
    owner(actor, app)
    db.commit()
    pdf = inspect_pdf(body.attachment, body.document_digest)
    return append(db, actor, aid, key, body, body.previous_id, pdf)


@router.post("/{aid}/attachments/{rid}/remove")
def remove(
    aid: UUID, rid: UUID, body: Change, request: Request, key: Key, db: DB, actor: Current
) -> CommandResult:
    mutation_guard(request, actor)
    return append(db, actor, aid, key, body, rid, None)


@router.get("/{aid}/attachments/{rid}/content")
def download(aid: UUID, rid: UUID, db: DB, actor: Current) -> Response:
    actor = common.refresh(db, actor)
    app = read_app(db, actor, aid)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "PRIVATE_APPLICATION_EVIDENCE")
    row = db.get(EvidenceRevision, rid)
    if not row or row.application_id != aid or row.scan == "REMOVED":
        raise HTTPException(404, "ATTACHMENT_NOT_FOUND")
    if row.scan != "CLEAN":
        raise HTTPException(423, "DOCUMENT_QUARANTINED_AWAITING_SCAN")
    content = row.content
    common.event(
        db,
        actor,
        rid,
        "APPLICATION_ATTACHMENT_DOWNLOAD",
        {"application_id": str(aid)},
        app.department_id,
    )
    db.commit()
    return Response(
        content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="application-evidence.pdf"',
            "Cache-Control": "private, no-store",
        },
    )
