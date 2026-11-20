from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from akus.exceptions.schemas import IST, CertificateProof, Proof


class Claim(Proof):
    expected_version: int = Field(ge=0)
    actual_exam_on: date
    certificate_key: str | None = Field(None, min_length=3, max_length=220)
    issued_on: date | None = None
    score_percent: float | None = Field(None, ge=0, le=100)
    sitting: str = Field(min_length=2, max_length=160)
    subject_id: UUID | None = None

    @model_validator(mode="after")
    def chronology(self) -> "Claim":
        today = self.observed_at.astimezone(IST).date()
        if self.actual_exam_on > today or (
            self.issued_on and not self.actual_exam_on <= self.issued_on <= today
        ):
            raise ValueError("Check actual exam, issue and observation dates")
        return self


class Attachment(BaseModel):
    media_type: Literal["application/pdf"]
    base64_data: str = Field(min_length=8, max_length=2796204)


class Registration(Claim):
    attachment: Attachment | None = None


class ExamProof(Proof):
    expected_version: int = Field(ge=1)
    actual_exam_on: date
    actual_exam_at: datetime | None = None
    sitting: str = Field(min_length=2, max_length=160)
    checked_person_offering_attendance: Literal[True]

    @model_validator(mode="after")
    def exam_date(self) -> "ExamProof":
        if (
            self.actual_exam_on > self.observed_at.astimezone(IST).date()
            or self.actual_exam_at
            and (
                not self.actual_exam_at.tzinfo
                or self.actual_exam_at > self.observed_at
                or self.actual_exam_at.astimezone(IST).date() != self.actual_exam_on
            )
        ):
            raise ValueError("The actual sitting must agree with the observed record")
        return self


class Verify(CertificateProof):
    expected_version: int = Field(ge=0)
    sitting: str = Field(min_length=2, max_length=160)
    credential_grade: str | None = Field(None, max_length=120)


class Disposition(Proof):
    expected_version: int = Field(ge=0)
    outcome: Literal["REJECTED", "REVOKED"]
    independently_checked: Literal[True]


class Capture(BaseModel):
    episode_id: UUID
