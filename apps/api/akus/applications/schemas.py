from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from akus.catalog.schemas import Decision


class Declarations(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score_sharing_yes: bool = False
    not_yet_enrolled: bool = False
    prior_attempt: Literal["NONE_DECLARED", "OUTCOME_UNVERIFIED", "VALID_CERTIFICATE"] = (
        "OUTCOME_UNVERIFIED"
    )
    emerging_technology_exception: bool = False
    acknowledgement: bool = False


class DraftWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offering_id: UUID
    declarations: Declarations
    id: UUID | None = None
    expected_version: int | None = None


class Submit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)
    snapshot_id: UUID
    mapping_revision_id: UUID | None = None


class Review(Decision):
    expected_version: int = Field(ge=1)
    decision: Literal["APPROVE", "REJECT"]


class Withdraw(Decision):
    expected_version: int = Field(ge=1)
    not_enrolled_declaration: bool


class Recheck(Decision):
    pass


class ScheduleClaim(Decision):
    """An assertion only; verification authority is not inferred from office rank."""

    scheduled_exam_on: date
    document_digest: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")


class VerifySchedule(Decision):
    expected_version: int = Field(ge=0)
    scheduled_exam_on: date
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime
    authenticated_official_person_and_offering: Literal[True]

    @model_validator(mode="after")
    def valid_observation(self) -> "VerifySchedule":
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(UTC):
            raise ValueError("An actual timezone-aware observation time is required")
        return self
