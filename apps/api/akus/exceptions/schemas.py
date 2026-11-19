from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from akus.catalog.schemas import Decision

IST = ZoneInfo("Asia/Kolkata")


class Proof(Decision):
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime

    @model_validator(mode="after")
    def actual(self) -> "Proof":
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(UTC):
            raise ValueError("Provide the actual timezone-aware observation time")
        return self


class Order(Proof):
    effective_on: date
    effective_at: datetime | None = None
    permanent_order_confirmed: Literal[True]

    @model_validator(mode="after")
    def precision(self) -> "Order":
        if self.effective_at and (
            self.effective_at.tzinfo is None
            or self.effective_at.astimezone(IST).date() != self.effective_on
        ):
            raise ValueError("Effective instant must match official local date")
        return self


class Closure(Proof):
    expected_event_id: UUID
    finding: Literal["Q44", "INDETERMINATE", "BEFORE_START", "AFTER_START", "UPHOLD", "INVALIDATE"]
    independently_checked: Literal[True]
    commencement_at: datetime | None = None
    separation_at: datetime | None = None
    enrollment_at: datetime | None = None
    enrollment_on: date | None = Field(None, exclude_if=lambda value: value is None)

    @model_validator(mode="after")
    def times(self) -> "Closure":
        if self.enrollment_on and (
            self.enrollment_at or self.enrollment_on > self.observed_at.astimezone(IST).date()
        ):
            raise ValueError(
                "Use the enrollment date or exact instant at the precision of the observed record"
            )
        if any(
            value and (value.tzinfo is None or value > self.observed_at)
            for value in (self.commencement_at, self.separation_at, self.enrollment_at)
        ):
            raise ValueError("Use observed timezone-aware event times")
        return self


class CertificateProof(Proof):
    certificate_key: str = Field(min_length=3, max_length=220, pattern=r"^\S(.*\S)?$")
    actual_exam_on: date
    actual_exam_at: datetime | None = None
    issued_on: date
    score_percent: float = Field(ge=0, le=100)
    subject_id: UUID | None = None
    relevance_basis: str | None = Field(None, min_length=5, max_length=1500)
    checked_person_offering_certificate: Literal[True]
    verified_exam_and_score_sharing: Literal[True]

    @model_validator(mode="after")
    def chronology(self) -> "CertificateProof":
        if not self.actual_exam_on <= self.issued_on <= self.observed_at.astimezone(IST).date():
            raise ValueError("Check the exam, issuance and observation dates")
        if self.actual_exam_at and (
            not self.actual_exam_at.tzinfo
            or self.actual_exam_on != self.actual_exam_at.astimezone(IST).date()
            or self.actual_exam_at > self.observed_at
        ):
            raise ValueError("Exact exam instant must match the observed exam date")
        if bool(self.subject_id) != bool(self.relevance_basis):
            raise ValueError("A subject assessment requires its specific relevance evidence")
        return self


class RosterProof(Proof):
    expected_event_id: UUID
    checked_complete_person_offering_roster: Literal[True]
    absence_through: datetime

    @model_validator(mode="after")
    def actual_coverage(self) -> "RosterProof":
        if self.absence_through.tzinfo is None or self.absence_through > self.observed_at:
            raise ValueError("Coverage must end at a documented instant already observed")
        return self


class SubjectProof(Proof):
    finding_id: UUID
    subject_id: UUID
    relevance_basis: str = Field(min_length=5, max_length=1500)
    checked_subject_relevance: Literal[True]
