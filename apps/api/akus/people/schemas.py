from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class DepartmentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str


class StaffCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    staff_key: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{1,39}$")
    display_name: str = Field(min_length=2, max_length=120)
    department_id: UUID
    starts_on: date
    is_faculty: bool
    source_reference: str = Field(min_length=3, max_length=300)
    reason: str = Field(min_length=5, max_length=1000)


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    person_id: UUID
    office: Literal["DRC_HEAD", "HOD", "ACTING_HOD", "PRINCIPAL"]
    department_id: UUID | None = None
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None = None
    source_reference: str = Field(min_length=3, max_length=300)
    reason: str = Field(min_length=5, max_length=1000)

    @model_validator(mode="after")
    def interval_and_scope(self) -> "AppointmentCreate":
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("End must be after start")
        if (self.office == "PRINCIPAL") != (self.department_id is None):
            raise ValueError(
                "Principal requires institution scope; other offices require department"
            )
        return self


class AppointmentEnd(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=1000)


class CommandResult(BaseModel):
    id: UUID


class StaffSummary(BaseModel):
    id: UUID
    staff_key: str
    display_name: str
    department: str | None
    department_id: UUID | None
    employment_status: str
    offices: list[str]


class StaffPage(BaseModel):
    items: list[StaffSummary]
    total: int
    offset: int
    limit: int


class EpisodeView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    starts_on: date
    ends_before: date | None
    is_faculty: bool
    source_reference: str
    recorded_at: datetime


class AppointmentView(BaseModel):
    id: UUID
    person_id: UUID
    person_name: str
    office: str
    department_id: UUID | None
    department: str | None
    valid_from: datetime
    valid_until: datetime | None
    original_until: datetime | None
    source_reference: str
    reason: str
    recorded_at: datetime
    version: int
    status: str


class AppointmentPage(BaseModel):
    items: list[AppointmentView]
    total: int
    offset: int
    limit: int


class HistoryEvent(BaseModel):
    id: UUID
    action: str
    recorded_at: datetime
    details: dict[str, str]


class StaffDetail(BaseModel):
    person: StaffSummary
    source_reference: str
    recorded_at: datetime
    episodes: list[EpisodeView]
    appointments: list[AppointmentView]
    events: list[HistoryEvent]
