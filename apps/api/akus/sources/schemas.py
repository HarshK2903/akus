from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class SourceCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_reference: str = Field(min_length=3, max_length=300)
    reason: str = Field(min_length=5, max_length=1000)


class TeachingWrite(SourceCommand):
    external_key: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{1,99}$")
    episode_id: UUID
    subject_id: UUID
    department_id: UUID
    academic_year_id: UUID
    term: str = Field(min_length=2, max_length=60)
    starts_on: date
    ends_before: date
    voided: bool = False
    expected_version: int | None = Field(None, ge=1)

    @model_validator(mode="after")
    def interval(self) -> "TeachingWrite":
        if self.ends_before <= self.starts_on:
            raise ValueError("End must follow start")
        return self


class ReferenceWrite(SourceCommand):
    kind: Literal["department", "subject", "alias", "year"]
    id: UUID | None = None
    expected_version: int | None = Field(None, ge=1)
    code: str = Field(default="", max_length=40)
    name: str = Field(default="", max_length=160)
    starts_on: date | None = None
    subject_id: UUID | None = None


class SourceChange(SourceCommand):
    kind: Literal["person", "employment", "department", "email", "office"]
    id: UUID | None = None
    expected_version: int | None = Field(None, ge=1)
    values: dict[str, Any]


class PersonFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(min_length=2, max_length=120)
    enabled: bool


class EmploymentFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    starts_on: date
    ends_before: date | None = None
    is_faculty: bool

    @model_validator(mode="after")
    def interval(self) -> "EmploymentFacts":
        if self.ends_before and self.ends_before <= self.starts_on:
            raise ValueError("End must follow start")
        return self


class DepartmentFacts(EmploymentFacts):
    episode_id: UUID
    department_id: UUID
    is_faculty: bool = False  # ignored; home membership never grants faculty eligibility


class EmailFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def interval(self) -> "EmailFacts":
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("End must follow start")
        return self
