from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from akus.catalog.schemas import Decision

Outcome = Literal["NO_VALID_CERT", "VALID_CERT", "UNRESOLVED"]


class AttemptWrite(Decision):
    offering_id: UUID
    expected_version: int = Field(ge=0)
    asserted_outcome: Outcome
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime

    @model_validator(mode="after")
    def valid_time(self) -> "AttemptWrite":
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(UTC):
            raise ValueError("Actual timezone-aware evidence observation required")
        return self


class OutcomeDecision(Decision):
    evidence_id: UUID
    expected_version: int = Field(ge=0)
    outcome: Outcome
    concluded_on: date | None = None
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime
    independently_authenticated_person_and_run: Literal[True]
    conclusive_official_result: bool

    @model_validator(mode="after")
    def valid_result(self) -> "OutcomeDecision":
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(UTC):
            raise ValueError("Actual timezone-aware observation required")
        if self.outcome != "UNRESOLVED" and (
            not self.conclusive_official_result or not self.concluded_on
        ):
            raise ValueError("Conclusive official result and actual conclusion date required")
        if (
            self.concluded_on
            and self.concluded_on > self.observed_at.astimezone(ZoneInfo("Asia/Kolkata")).date()
        ):
            raise ValueError("Future conclusion cannot be verified")
        return self
