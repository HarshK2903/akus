from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from akus.catalog.schemas import Decision


class EnrollmentProof(Decision):
    expected_version: int = Field(ge=0)
    enrolled_at: datetime | None = None
    enrolled_on: date | None = None
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime

    @model_validator(mode="after")
    def valid_dates(self) -> "EnrollmentProof":
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(UTC):
            raise ValueError("A timezone-aware actual observation time is required")
        if (self.enrolled_at is None) == (self.enrolled_on is None):
            raise ValueError(
                "Supply one exact time or date-only value, preserving source precision"
            )
        if self.enrolled_at and (
            self.enrolled_at.tzinfo is None or self.enrolled_at > self.observed_at
        ):
            raise ValueError("Enrollment time must be timezone-aware and no later than observation")
        if (
            self.enrolled_on
            and self.enrolled_on > self.observed_at.astimezone(ZoneInfo("Asia/Kolkata")).date()
        ):
            raise ValueError("Enrollment date cannot be after source observation")
        return self


class EnrollmentVerify(EnrollmentProof):
    claim_id: UUID
    outcome: Literal["VERIFIED", "UNRESOLVED", "REJECTED"]
    independently_authenticated: Literal[True]


class RequestWithdrawal(Decision):
    expected_version: int = Field(ge=1)
    voluntary_request: Literal[True]


class DecideWithdrawal(Decision):
    request_id: UUID
    expected_version: int = Field(ge=1)
    decision: Literal["AUTHORIZE", "DENY"]
    independently_checked: Literal[True]
