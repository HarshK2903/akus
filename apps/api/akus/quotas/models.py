from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class QuotaPool(Base):
    __tablename__ = "department_topic_quotas"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("nptel_topics.id", ondelete="RESTRICT"))
    academic_year_id: Mapped[UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="RESTRICT")
    )
    maximum: Mapped[int] = mapped_column()
    occupied: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    version: Mapped[int] = mapped_column(default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint(
            "department_id", "topic_id", "academic_year_id", name="one_annual_shared_topic_pool"
        ),
        CheckConstraint(
            "maximum >= 0 AND occupied >= 0 AND occupied <= maximum", name="quota_capacity_bounds"
        ),
        CheckConstraint("status IN ('DRAFT','PUBLISHED')"),
        CheckConstraint("status <> 'DRAFT' OR occupied = 0"),
    )


class QuotaRevision(Base):
    __tablename__ = "topic_quota_revisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    pool_id: Mapped[UUID] = mapped_column(
        ForeignKey("department_topic_quotas.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column()
    previous_maximum: Mapped[int | None] = mapped_column()
    maximum: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    office_id: Mapped[UUID] = mapped_column(
        ForeignKey("office_appointments.id", ondelete="RESTRICT")
    )
    reason: Mapped[str] = mapped_column(String(2000))
    source_reference: Mapped[str] = mapped_column(String(500))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("pool_id", "version", name="quota_revision_unique"),)
