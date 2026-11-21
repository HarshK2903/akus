from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class SourceRevision(Base):
    __tablename__ = "source_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[UUID] = mapped_column(index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any]] = mapped_column(JSONB)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )


class Subject(Base):
    __tablename__ = "canonical_subjects"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    source_reference: Mapped[str] = mapped_column(String(300))
    version: Mapped[int] = mapped_column(default=1)


class SubjectAlias(Base):
    __tablename__ = "subject_aliases"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_subjects.id", ondelete="RESTRICT")
    )
    alias: Mapped[str] = mapped_column(String(160))
    source_reference: Mapped[str] = mapped_column(String(300))
    __table_args__ = (UniqueConstraint("alias", name="unique_subject_alias"),)


class TeachingAssignment(Base):
    __tablename__ = "teaching_assignments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    external_key: Mapped[str] = mapped_column(String(100), unique=True)
    episode_id: Mapped[UUID] = mapped_column(
        ForeignKey("employment_episodes.id", ondelete="RESTRICT"), index=True
    )
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_subjects.id", ondelete="RESTRICT")
    )
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    academic_year_id: Mapped[UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="RESTRICT")
    )
    term: Mapped[str] = mapped_column(String(60))
    starts_on: Mapped[date] = mapped_column()
    ends_before: Mapped[date] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(300))
    voided: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("ends_before > starts_on", name="teaching_interval"),
        ExcludeConstraint(
            ("episode_id", "="),
            ("subject_id", "="),
            ("department_id", "="),
            (func.daterange(starts_on, ends_before, "[)"), "&&"),
            where="NOT voided",
            using="gist",
            name="no_duplicate_teaching_interval",
        ),
    )


class SourceImport(Base):
    __tablename__ = "source_imports"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(150))
    content_hash: Mapped[str] = mapped_column(String(64))
    source_reference: Mapped[str] = mapped_column(String(300))
    rows: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="STAGED")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("kind", "content_hash", "source_reference", name="source_import_dedupe"),
    )
