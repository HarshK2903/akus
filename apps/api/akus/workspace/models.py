"""In-app presentation and acknowledgement records, independent of academic decisions."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class NoticeTemplate(Base):
    __tablename__ = "notice_template_versions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(18))
    version: Mapped[int]
    heading: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(String(500))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
    __table_args__ = (UniqueConstraint("category", "version", name="one_notice_template_version"),)


class PersonalNotice(Base):
    __tablename__ = "personal_test_notices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"), index=True)
    category: Mapped[str] = mapped_column(String(18))
    heading: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )


class NoticeRead(Base):
    __tablename__ = "personal_notice_reads"
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"), primary_key=True)
    notice_id: Mapped[UUID] = mapped_column(primary_key=True)
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )


class NoticePreference(Base):
    __tablename__ = "personal_notice_preferences"
    person_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id"), primary_key=True)
    initial_filter: Mapped[str] = mapped_column(String(10))
    __table_args__ = (CheckConstraint("initial_filter IN ('ALL','UNREAD')"),)
