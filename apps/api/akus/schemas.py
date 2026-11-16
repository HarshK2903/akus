from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DemoLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_key: str = Field(min_length=1, max_length=40)


class Identity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    key: str
    name: str
    role: str
    department: str
    mode: Literal["LOCAL_DEMO", "INSTITUTIONAL"] = "LOCAL_DEMO"
    person_id: UUID | None = None
    roles: list[str] = Field(default_factory=list)
    department_ids: list[UUID] = Field(default_factory=list)
    can_manage_people: bool = False
    can_read_directory: bool = False
    applicant_eligible: bool = False


class LoginResult(BaseModel):
    identity: Identity
    csrf_token: str


class Year(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    label: str
    starts_on: date
    ends_on: date
    source: str


class Health(BaseModel):
    status: str
    database: str | None = None
    schema_version: str | None = None


class AuthConfig(BaseModel):
    demo_enabled: bool
    google_enabled: bool = False
    institution_label: str


class Foundation(BaseModel):
    phase: int = 1
    database: Literal["connected"] = "connected"
    worker: str
    worker_seen_at: datetime | None
    google: Literal["not_configured", "configured"] = "not_configured"
    nptel: Literal["not_connected"] = "not_connected"
    institution_label: str
    checked_at: datetime


class PolicyHelp(BaseModel):
    id: str
    title: str
    status: str
    summary: str
