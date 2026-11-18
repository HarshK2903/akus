from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=5, max_length=2000)
    source_reference: str = Field(min_length=3, max_length=500)


class CourseWrite(Decision):
    id: UUID | None = None
    expected_version: int | None = Field(None, ge=1)
    code: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,79}$")
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(default="", max_length=12000)


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(default="", max_length=12000)
    categories: list[str] = Field(min_length=1, max_length=30)
    duration_weeks: int | None = Field(None, ge=1, le=104)
    starts_on: date | None = None
    ends_on: date | None = None
    enrollment_ends_on: date | None = None
    exam_registration_ends_on: date | None = None
    scheduled_exam_on: date | None = None
    timezone: Literal["Asia/Kolkata"] = "Asia/Kolkata"
    precision: Literal["DATE"] = "DATE"

    @model_validator(mode="after")
    def check(self) -> "Metadata":
        self.categories = list(dict.fromkeys(s.strip() for s in self.categories))
        if any(not s or len(s) > 160 or "<" in s or ">" in s for s in self.categories):
            raise ValueError("Invalid provider category")
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("Invalid course interval")
        if self.starts_on and self.scheduled_exam_on and self.scheduled_exam_on < self.starts_on:
            raise ValueError("Exam precedes course")
        return self


class OfferingFetch(Decision):
    course_id: UUID
    provider_id: str = Field(pattern=r"^noc\d{2}_[a-z0-9]{2,30}$")


class DemoOffering(Decision):
    course_id: UUID
    provider_id: str = Field(pattern=r"^LOCAL_[A-Za-z0-9_-]{2,60}$")
    metadata: Metadata


class SnapshotAccept(Decision):
    snapshot_id: UUID
    expected_version: int = Field(ge=0)


class TopicWrite(Decision):
    id: UUID | None = None
    expected_version: int | None = Field(None, ge=1)
    code: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{1,39}$")
    name: str = Field(min_length=2, max_length=160)


class AliasWrite(Decision):
    topic_id: UUID
    label: str = Field(min_length=2, max_length=160)


class ProposalWrite(Decision):
    label: str = Field(min_length=2, max_length=160)


class ProposalResolve(Decision):
    topic_id: UUID


class MappingWrite(Decision):
    topic_id: UUID
    snapshot_id: UUID
    expected_version: int = Field(ge=0)


class MappingIntake(Decision):
    offering_id: UUID


class QuotaWrite(Decision):
    topic_id: UUID
    academic_year_id: UUID
    maximum: int = Field(ge=0, le=2147483647)
    publish: bool = False
    expected_version: int = Field(default=0, ge=0)
