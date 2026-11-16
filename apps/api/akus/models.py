from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class DemoIdentity(Base):
    """Fictional fixtures only; never an institutional staff/office authority table."""

    __tablename__ = "demo_identities"
    __table_args__ = (CheckConstraint("role IN ('FACULTY','DRC_HEAD','HOD','PRINCIPAL','ADMIN')"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    department: Mapped[str] = mapped_column(String(100))


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    identity_id: Mapped[UUID] = mapped_column(ForeignKey("demo_identities.id", ondelete="RESTRICT"))
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (
        CheckConstraint("EXTRACT(MONTH FROM starts_on)=7 AND EXTRACT(DAY FROM starts_on)=1"),
        CheckConstraint("ends_on = (starts_on + INTERVAL '1 year' - INTERVAL '1 day')::date"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    label: Mapped[str] = mapped_column(String(20), unique=True)
    starts_on: Mapped[date] = mapped_column(unique=True)
    ends_on: Mapped[date] = mapped_column(unique=True)
    source: Mapped[str] = mapped_column(String(300), default="LOCAL_DEMO_FIXTURE")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("demo_identities.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(60))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    details: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)


class WorkJob(Base):
    __tablename__ = "work_jobs"
    __table_args__ = (CheckConstraint("state IN ('PENDING','DONE','DEAD')"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(16), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
