from datetime import datetime
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
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class InstitutionalEmail(Base):
    __tablename__ = "institutional_emails"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), index=True
    )
    email: Mapped[str] = mapped_column(String(254))
    normalized_email: Mapped[str] = mapped_column(String(254))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_reference: Mapped[str] = mapped_column(String(300))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("normalized_email=lower(email)", name="email_normalized"),
        CheckConstraint("valid_until IS NULL OR valid_until > valid_from", name="email_interval"),
        # Conflicting historical source entries may be retained; linking must detect ambiguity.
        Index("ix_institutional_email_match", "normalized_email"),
    )


class ExternalIdentity(Base):
    __tablename__ = "external_identities"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    issuer: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(255))
    linked_email: Mapped[str] = mapped_column(String(254))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="one_subject_identity"),
        Index(
            "one_live_identity_per_person",
            "person_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )


class InstitutionalSession(Base):
    __tablename__ = "institutional_sessions"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    person_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), index=True
    )
    external_identity_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_identities.id", ondelete="RESTRICT")
    )
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OidcFlow(Base):
    __tablename__ = "oidc_flows"
    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    browser_hash: Mapped[str] = mapped_column(String(64))
    peer_hash: Mapped[str] = mapped_column(String(64), index=True)
    nonce: Mapped[str] = mapped_column(String(100))
    encrypted_verifier: Mapped[str] = mapped_column(String(400))
    return_to: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountRequest(Base):
    __tablename__ = "account_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    issuer: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    person_id: Mapped[UUID | None] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    reason: Mapped[str] = mapped_column(
        String(1000), default="Verified Google identity requires an approved roster record"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("issuer", "subject", name="one_account_request"),)


class VerifiedEmailObservation(Base):
    """Provider-verified email history; never edits the authoritative institutional roster."""

    __tablename__ = "verified_email_observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    external_identity_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_identities.id", ondelete="RESTRICT")
    )
    email: Mapped[str] = mapped_column(String(254))
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("external_identity_id", "email", name="verified_email_observation_once"),
    )
