"""Append-only application assertions, independent findings and review history."""

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class DraftRevision(Base):
    __tablename__ = "application_draft_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    version: Mapped[int] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    declarations: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("application_id", "version", name="draft_revision_once"),)


class EnrollmentClaim(Base):
    __tablename__ = "enrollment_claims"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    version: Mapped[int] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrolled_on: Mapped[date | None] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("application_id", "version", name="enrollment_claim_version_once"),
        CheckConstraint("(enrolled_at IS NULL) <> (enrolled_on IS NULL)"),
    )


class EnrollmentFinding(Base):
    __tablename__ = "enrollment_findings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    claim_id: Mapped[UUID] = mapped_column(ForeignKey("enrollment_claims.id"))
    version: Mapped[int] = mapped_column()
    outcome: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    office_id: Mapped[UUID] = mapped_column(ForeignKey("office_appointments.id"))
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrolled_on: Mapped[date | None] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(500))
    document_digest: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("application_id", "version", name="enrollment_finding_version_once"),
        CheckConstraint("outcome IN ('VERIFIED','UNRESOLVED','REJECTED')"),
        CheckConstraint("(enrolled_at IS NULL) <> (enrolled_on IS NULL)"),
    )


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    source_reference: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WithdrawalDecision(Base):
    __tablename__ = "withdrawal_decisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("withdrawal_requests.id"), unique=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    office_id: Mapped[UUID] = mapped_column(ForeignKey("office_appointments.id"))
    decision: Mapped[str] = mapped_column(String(20))
    finding_id: Mapped[UUID | None] = mapped_column(ForeignKey("enrollment_findings.id"))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (CheckConstraint("decision IN ('AUTHORIZE','DENY')"),)


class ReviewDecision(Base):
    __tablename__ = "application_review_decisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    office_id: Mapped[UUID] = mapped_column(ForeignKey("office_appointments.id"))
    stage: Mapped[str] = mapped_column(String(20))
    decision: Mapped[str] = mapped_column(String(20))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (CheckConstraint("decision IN ('APPROVE','REJECT')"),)
