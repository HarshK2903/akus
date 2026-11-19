"""Permanent-person canonical attempt identity and append-only source findings."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class Attempt(Base):
    __tablename__ = "nptel_attempts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"), index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_courses.id"))
    offering_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_offerings.id"))
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("person_id", "offering_id", name="one_person_run_attempt"),)


class AttemptEvidence(Base):
    __tablename__ = "attempt_evidence"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_attempts.id"), index=True)
    version: Mapped[int] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    asserted_outcome: Mapped[str] = mapped_column(String(20))
    source_reference: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("attempt_id", "version", name="attempt_evidence_version_once"),
        CheckConstraint("asserted_outcome IN ('NO_VALID_CERT','VALID_CERT','UNRESOLVED')"),
    )


class OutcomeFinding(Base):
    __tablename__ = "outcome_findings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_attempts.id"), index=True)
    evidence_id: Mapped[UUID] = mapped_column(ForeignKey("attempt_evidence.id"))
    version: Mapped[int] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    office_id: Mapped[UUID] = mapped_column(ForeignKey("office_appointments.id"))
    outcome: Mapped[str] = mapped_column(String(20))
    concluded_on: Mapped[date | None] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("attempt_id", "version", name="outcome_finding_version_once"),
        CheckConstraint("outcome IN ('NO_VALID_CERT','VALID_CERT','UNRESOLVED')"),
        CheckConstraint("outcome='UNRESOLVED' OR concluded_on IS NOT NULL"),
    )
