from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class CredentialMandate(Base):
    """Externally issued designation covering one application and optionally one subject."""

    __tablename__ = "credential_mandates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("canonical_subjects.id"))
    basis: Mapped[str] = mapped_column(String(500))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("valid_from < valid_until AND length(trim(basis)) >= 5"),)


class CredentialDocument(Base):
    __tablename__ = "credential_documents"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    content: Mapped[bytes]
    scan: Mapped[str] = mapped_column(String(20))
    __table_args__ = (CheckConstraint("octet_length(content) BETWEEN 1 AND 2097152"),)


class CredentialEvent(Base):
    __tablename__ = "credential_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"))
    version: Mapped[int]
    kind: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    mandate_id: Mapped[UUID | None] = mapped_column(ForeignKey("credential_mandates.id"))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("credential_documents.id"))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("application_id", "version"),
        Index("ix_credential_as_of", "application_id", "recorded_at"),
        CheckConstraint(
            "kind IN ('ASSERTED','EXAM_VERIFIED','VERIFIED','REJECTED','REVOKED') AND (kind='ASSERTED')=(mandate_id IS NULL)"
        ),
    )


class CredentialIdentity(Base):
    """A provider identifier stays bound to its original run even if its result is revoked."""

    __tablename__ = "credential_identities"
    certificate_key: Mapped[str] = mapped_column(String(220), primary_key=True)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), index=True)


class AssessmentSnapshot(Base):
    __tablename__ = "compliance_snapshots"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("employment_episodes.id"))
    digest: Mapped[str] = mapped_column(String(64))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (Index("ix_compliance_snapshot_time", "episode_id", "recorded_at"),)
