from datetime import datetime
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
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class Course(Base):
    __tablename__ = "nptel_courses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(String(12000), default="")
    source_reference: Mapped[str] = mapped_column(String(500))
    version: Mapped[int] = mapped_column(default=1)


class Offering(Base):
    __tablename__ = "nptel_offerings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("nptel_courses.id", ondelete="RESTRICT"), index=True
    )
    provider_id: Mapped[str] = mapped_column(String(80), unique=True)
    current_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "provider_snapshots.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="offering_current_snapshot_fk",
        )
    )
    version: Mapped[int] = mapped_column(default=0)
    source_status: Mapped[str] = mapped_column(String(40), default="NOT_CHECKED")


class ProviderSnapshot(Base):
    __tablename__ = "provider_snapshots"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    offering_id: Mapped[UUID] = mapped_column(
        ForeignKey("nptel_offerings.id", ondelete="RESTRICT"), index=True
    )
    digest: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[str] = mapped_column(String(500))
    trust: Mapped[str] = mapped_column(String(30))
    parser_version: Mapped[str] = mapped_column(String(40), default="nptel-preview-2026-11")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    __table_args__ = (CheckConstraint("trust IN ('OFFICIAL_HTTPS','LOCAL_DEMO')"),)


class ProviderFetch(Base):
    __tablename__ = "provider_fetches"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    offering_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_offerings.id", ondelete="RESTRICT"))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40))
    error_code: Mapped[str | None] = mapped_column(String(60))
    snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )


class Topic(Base):
    __tablename__ = "nptel_topics"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str] = mapped_column(String(160), unique=True)
    source_reference: Mapped[str] = mapped_column(String(500))
    version: Mapped[int] = mapped_column(default=1)


class TopicAlias(Base):
    __tablename__ = "nptel_topic_aliases"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    label: Mapped[str] = mapped_column(String(160))
    normalized_label: Mapped[str] = mapped_column(String(160), unique=True)
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_topics.id", ondelete="RESTRICT"))
    source_reference: Mapped[str] = mapped_column(String(500))


class TopicProposal(Base):
    __tablename__ = "nptel_topic_proposals"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    normalized_label: Mapped[str] = mapped_column(String(160))
    source_reference: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str] = mapped_column(String(2000))
    topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("nptel_topics.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("department_id", "normalized_label", name="deduplicate_topic_proposal"),
    )


class MappingAnchor(Base):
    __tablename__ = "department_course_mappings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_courses.id", ondelete="RESTRICT"))
    version: Mapped[int] = mapped_column(default=0)
    __table_args__ = (
        UniqueConstraint("department_id", "course_id", name="one_department_course_mapping"),
    )


class MappingRevision(Base):
    __tablename__ = "primary_topic_mapping_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    mapping_id: Mapped[UUID] = mapped_column(
        ForeignKey("department_course_mappings.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column()
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_topics.id", ondelete="RESTRICT"))
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    office_id: Mapped[UUID] = mapped_column(
        ForeignKey("office_appointments.id", ondelete="RESTRICT")
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(2000))
    source_reference: Mapped[str] = mapped_column(String(500))
    policy: Mapped[str] = mapped_column(String(80), default="V2.4")
    __table_args__ = (
        UniqueConstraint("mapping_id", "version", name="mapping_revision_unique"),
        Index(
            "one_current_primary_topic",
            "mapping_id",
            unique=True,
            postgresql_where=text("valid_until IS NULL"),
        ),
        CheckConstraint("valid_until IS NULL OR valid_until > valid_from"),
        ExcludeConstraint(
            ("mapping_id", "="),
            (func.tstzrange(valid_from, valid_until, "[)"), "&&"),
            using="gist",
            name="nonoverlapping_primary_mapping",
        ),
    )


class MappingRequest(Base):
    __tablename__ = "primary_topic_mapping_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_courses.id", ondelete="RESTRICT"))
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_snapshots.id", ondelete="RESTRICT")
    )
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(30), default="REVIEW_PENDING")
    reason: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint(
            "department_id", "course_id", "snapshot_id", name="deduplicate_mapping_request"
        ),
    )


class AcademicEvent(Base):
    __tablename__ = "academic_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_id: Mapped[UUID] = mapped_column(index=True)
    kind: Mapped[str] = mapped_column(String(60))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT")
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
