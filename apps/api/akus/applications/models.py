from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    episode_id: Mapped[UUID] = mapped_column(
        ForeignKey("employment_episodes.id", ondelete="RESTRICT")
    )
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_courses.id", ondelete="RESTRICT"))
    offering_id: Mapped[UUID] = mapped_column(
        ForeignKey("nptel_offerings.id", ondelete="RESTRICT"), index=True
    )
    state: Mapped[str] = mapped_column(String(24), default="DRAFT")
    version: Mapped[int] = mapped_column(default=1)
    declarations: Mapped[dict[str, Any]] = mapped_column(JSONB)
    next_office: Mapped[str | None] = mapped_column(String(20))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("state IN ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED','WITHDRAWN')"),
        Index(
            "one_active_canonical_application",
            "person_id",
            "course_id",
            unique=True,
            postgresql_where=text("state IN ('UNDER_REVIEW','APPROVED')"),
        ),
    )


class Submission(Base):
    __tablename__ = "application_submissions"
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), primary_key=True
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    mapping_revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("primary_topic_mapping_revisions.id", ondelete="RESTRICT")
    )
    original_pool_id: Mapped[UUID] = mapped_column(
        ForeignKey("department_topic_quotas.id", ondelete="RESTRICT")
    )
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Allocation(Base):
    __tablename__ = "quota_allocations"
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), primary_key=True
    )
    pool_id: Mapped[UUID] = mapped_column(
        ForeignKey("department_topic_quotas.id", ondelete="RESTRICT"), index=True
    )
    state: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(default=1)
    schedule_snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    personal_schedule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("personal_schedule_revisions.id", ondelete="RESTRICT")
    )
    __table_args__ = (CheckConstraint("state IN ('HELD','CONFIRMED','RETAINED','RELEASED')"),)


class Ledger(Base):
    __tablename__ = "quota_ledger"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    movement_id: Mapped[UUID] = mapped_column(index=True)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True
    )
    pool_id: Mapped[UUID] = mapped_column(
        ForeignKey("department_topic_quotas.id", ondelete="RESTRICT"), index=True
    )
    delta: Mapped[int] = mapped_column()
    kind: Mapped[str] = mapped_column(String(24))
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    personal_schedule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("personal_schedule_revisions.id", ondelete="RESTRICT")
    )
    __table_args__ = (
        CheckConstraint("delta BETWEEN -1 AND 1"),
        UniqueConstraint("movement_id", "pool_id", name="movement_pool_once"),
    )


class Reconciliation(Base):
    __tablename__ = "academic_reconciliations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True
    )
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    reason: Mapped[str] = mapped_column(String(100))
    snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    context: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("application_id", "kind", name="one_current_reconciliation"),
        CheckConstraint("status IN ('OPEN','RESOLVED')"),
    )


class AcademicNotice(Base):
    """Transactional in-app outbox: durable and visible after commit, never email delivery."""

    __tablename__ = "academic_notices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True
    )
    kind: Mapped[str] = mapped_column(String(60))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PersonalSchedule(Base):
    __tablename__ = "personal_schedule_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True
    )
    version: Mapped[int] = mapped_column()
    scheduled_exam_on: Mapped[date] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    office_id: Mapped[UUID] = mapped_column(
        ForeignKey("office_appointments.id", ondelete="RESTRICT")
    )
    reason: Mapped[str] = mapped_column(String(2000))
    __table_args__ = (
        UniqueConstraint("application_id", "version", name="one_personal_schedule_version"),
    )


class PersonalScheduleCurrent(Base):
    __tablename__ = "personal_schedule_current"
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), primary_key=True
    )
    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("personal_schedule_revisions.id", ondelete="RESTRICT")
    )
