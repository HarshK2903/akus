from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from akus.db import Base


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class Person(Base):
    __tablename__ = "persons"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    staff_key: Mapped[str] = mapped_column(String(40), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    demo_identity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("demo_identities.id", ondelete="RESTRICT"), unique=True
    )
    enabled: Mapped[bool] = mapped_column(default=True)
    source_reference: Mapped[str] = mapped_column(String(300))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EmploymentEpisode(Base):
    __tablename__ = "employment_episodes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), index=True
    )
    starts_on: Mapped[date] = mapped_column()
    ends_before: Mapped[date | None] = mapped_column()
    is_faculty: Mapped[bool]
    source_reference: Mapped[str] = mapped_column(String(300))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint(
            "ends_before IS NULL OR ends_before > starts_on", name="valid_employment_dates"
        ),
        ExcludeConstraint(
            ("person_id", "="),
            (func.daterange(starts_on, ends_before, "[)"), "&&"),
            name="employment_no_overlap",
            using="gist",
        ),
    )


class DepartmentAssignment(Base):
    __tablename__ = "faculty_department_appointments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column(
        ForeignKey("employment_episodes.id", ondelete="RESTRICT"), index=True
    )
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    starts_on: Mapped[date] = mapped_column()
    ends_before: Mapped[date | None] = mapped_column()
    source_reference: Mapped[str] = mapped_column(String(300))
    __table_args__ = (
        CheckConstraint(
            "ends_before IS NULL OR ends_before > starts_on", name="valid_department_dates"
        ),
        ExcludeConstraint(
            ("episode_id", "="),
            (func.daterange(starts_on, ends_before, "[)"), "&&"),
            name="one_home_department_at_time",
            using="gist",
        ),
    )


class OfficeAppointment(Base):
    __tablename__ = "office_appointments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), index=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT")
    )
    office: Mapped[str] = mapped_column(String(20))
    office_group: Mapped[str] = mapped_column(
        String(20),
        Computed("CASE WHEN office='ACTING_HOD' THEN 'HOD' ELSE office END", persisted=True),
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    original_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_reference: Mapped[str] = mapped_column(String(300))
    reason: Mapped[str] = mapped_column(String(1000))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    version: Mapped[int] = mapped_column(default=1)
    superseded: Mapped[bool] = mapped_column(default=False, server_default="false")
    __table_args__ = (
        CheckConstraint(
            "office IN ('DRC_HEAD','HOD','ACTING_HOD','PRINCIPAL')", name="valid_office"
        ),
        CheckConstraint(
            "(office='PRINCIPAL' AND department_id IS NULL) OR (office <> 'PRINCIPAL' AND department_id IS NOT NULL)",
            name="office_scope",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from", name="valid_office_interval"
        ),
        ExcludeConstraint(
            ("person_id", "="),
            ("office_group", "<>"),
            (func.tstzrange(valid_from, valid_until, "[)"), "&&"),
            where="office_group IN ('DRC_HEAD','HOD') AND NOT superseded",
            name="exclusive_drc_hod_globally",
            using="gist",
        ),
        ExcludeConstraint(
            ("person_id", "="),
            (func.tstzrange(valid_from, valid_until, "[)"), "&&"),
            where="office='PRINCIPAL' AND NOT superseded",
            name="no_duplicate_person_principal",
            using="gist",
        ),
        ExcludeConstraint(
            ("department_id", "="),
            ("office_group", "="),
            (func.tstzrange(valid_from, valid_until, "[)"), "&&"),
            where="NOT superseded",
            name="one_department_officeholder",
            using="gist",
        ),
    )


class AdministrativeGrant(Base):
    """Source-provisioned admin access; not a faculty/academic approval grant."""

    __tablename__ = "administrative_grants"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    person_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), index=True
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_reference: Mapped[str] = mapped_column(String(300))
    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from", name="valid_admin_interval"
        ),
    )


class CommandReceipt(Base):
    __tablename__ = "people_command_receipts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("persons.id", ondelete="RESTRICT"))
    key: Mapped[UUID]
    operation: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, str]] = mapped_column(JSONB)
    __table_args__ = (UniqueConstraint("actor_id", "key", name="one_people_command_per_key"),)
