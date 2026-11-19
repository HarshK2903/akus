from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class Departure(Base):
    """Permanent HR order. A generic episode end is insufficient."""

    __tablename__ = "permanent_departures"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("employment_episodes.id"), unique=True)
    effective_on: Mapped[date]
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    proof: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SeparationSnapshot(Base):
    __tablename__ = "separation_snapshots"
    departure_id: Mapped[UUID] = mapped_column(
        ForeignKey("permanent_departures.id"), primary_key=True
    )
    subjects: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CaseEvent(Base):
    __tablename__ = "exception_case_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("academic_reconciliations.id"), index=True)
    version: Mapped[int]
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("persons.id"))
    office_id: Mapped[UUID | None] = mapped_column(ForeignKey("office_appointments.id"))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("case_id", "version", name="exception_revision_once"),)


class IntegrityMandate(Base):
    """Only a separately ratified, case-specific institutional designation authorizes disposition."""

    __tablename__ = "integrity_mandates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("academic_reconciliations.id"))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    basis: Mapped[str] = mapped_column(String(500))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HistoricalMandate(Base):
    """Externally issued designation for exact-person certificate/participation checks.
    A relevance designation, when present, applies to exactly one canonical subject.
    """

    __tablename__ = "historical_evidence_mandates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("academic_reconciliations.id"))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("canonical_subjects.id"))
    purpose: Mapped[str] = mapped_column(
        String(24), default="CERTIFICATE", server_default="CERTIFICATE"
    )
    __table_args__ = (
        CheckConstraint("purpose IN ('CERTIFICATE','ENROLLMENT_ABSENCE')"),
        CheckConstraint("valid_from < valid_until AND length(trim(basis)) >= 3"),
    )
    basis: Mapped[str] = mapped_column(String(500))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HistoricalFinding(Base):
    __tablename__ = "historical_certificate_findings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), unique=True)
    mandate_id: Mapped[UUID] = mapped_column(ForeignKey("historical_evidence_mandates.id"))
    certificate_key: Mapped[str] = mapped_column(String(220), unique=True)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ArchivedObligation(Base):
    """A previously adjudicated institutional obligation, distinct from a teaching row."""

    __tablename__ = "archived_subject_obligations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("employment_episodes.id"))
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_subjects.id"))
    first_assignment: Mapped[date]
    decided_on: Mapped[date]
    decision_reference: Mapped[str] = mapped_column(String(500))
    authority_basis: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("episode_id", "subject_id", name="one_archived_obligation"),
        CheckConstraint(
            "document_digest ~ '^[0-9a-f]{64}$' AND length(trim(authority_basis)) >= 5 AND length(trim(decision_reference)) >= 3"
        ),
    )
