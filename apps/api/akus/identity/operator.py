"""Operator-only first Admin setup. Never exposes a web grant endpoint or login bypass."""

import argparse
import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from akus.config import Settings
from akus.db import database
from akus.identity.models import InstitutionalEmail
from akus.identity.service import security_event, serialize_links
from akus.people.models import (
    AdministrativeGrant,
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    Person,
)


class BootstrapRoster(BaseModel):
    model_config = ConfigDict(extra="forbid")
    staff_key: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{1,39}$")
    display_name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^\s@]+@cmrit\.ac\.in$", max_length=254)
    department_code: str = Field(pattern=r"^[A-Z0-9_-]{2,30}$")
    department_name: str = Field(min_length=2, max_length=120)
    employment_starts_on: date
    authorized_from: datetime
    source_reference: str = Field(min_length=10, max_length=300)


def bootstrap(db: Session, cfg: Settings, row: BootstrapRoster) -> str:
    if cfg.demo_enabled:
        raise ValueError("Disable demo access before provisioning institutional staff")
    if row.authorized_from.tzinfo is None:
        raise ValueError("Authorization instant must include timezone")
    if row.authorized_from.date() < row.employment_starts_on:
        raise ValueError("Admin authorization cannot precede the approved employment episode")
    serialize_links(db)
    grant_id = uuid5(NAMESPACE_URL, "akus:first-admin:" + row.staff_key)
    previous = db.get(AdministrativeGrant, grant_id)
    if previous:
        person = db.get(Person, previous.person_id)
        email = db.scalar(
            select(InstitutionalEmail).where(InstitutionalEmail.person_id == previous.person_id)
        )
        episode = db.scalar(
            select(EmploymentEpisode).where(EmploymentEpisode.person_id == previous.person_id)
        )
        membership = (
            db.scalar(
                select(DepartmentAssignment).where(DepartmentAssignment.episode_id == episode.id)
            )
            if episode
            else None
        )
        department = db.get(Department, membership.department_id) if membership else None
        if (
            not episode
            or episode.starts_on != row.employment_starts_on
            or not department
            or department.code != row.department_code
            or department.name != row.department_name
            or previous.valid_from != row.authorized_from
            or not person
            or not email
            or person.display_name != row.display_name
            or email.email != row.email
            or previous.source_reference != row.source_reference
        ):
            raise ValueError(
                "Bootstrap already exists with different facts; use audited correction"
            )
        return "ALREADY_PROVISIONED" if previous.valid_until is None else "REVOKED"
    if db.scalar(
        select(AdministrativeGrant.id)
        .join(Person)
        .where(Person.demo_identity_id.is_(None))
        .limit(1)
    ):
        raise ValueError("Institutional Admin already provisioned; use current Admin governance")
    if db.scalar(select(Person.id).where(Person.staff_key == row.staff_key)):
        raise ValueError("Existing staff identity requires explicit reconciliation")
    department = db.scalar(select(Department).where(Department.code == row.department_code))
    if not department:
        department = Department(code=row.department_code, name=row.department_name)
        db.add(department)
        db.flush()
    elif department.name != row.department_name:
        raise ValueError("Department source mismatch")
    person = Person(
        staff_key=row.staff_key,
        display_name=row.display_name,
        source_reference=row.source_reference,
    )
    db.add(person)
    db.flush()
    episode = EmploymentEpisode(
        person_id=person.id,
        starts_on=row.employment_starts_on,
        is_faculty=False,
        source_reference=row.source_reference,
    )
    db.add(episode)
    db.flush()
    db.add(
        DepartmentAssignment(
            episode_id=episode.id,
            department_id=department.id,
            starts_on=row.employment_starts_on,
            source_reference=row.source_reference,
        )
    )
    db.add(
        InstitutionalEmail(
            person_id=person.id,
            email=row.email,
            normalized_email=row.email.lower(),
            valid_from=row.authorized_from,
            source_reference=row.source_reference,
        )
    )
    db.add(
        AdministrativeGrant(
            id=grant_id,
            person_id=person.id,
            valid_from=row.authorized_from,
            source_reference=row.source_reference,
        )
    )
    security_event(
        db,
        "FIRST_ADMIN_PROVISIONED",
        person_id=str(person.id),
        source_reference=row.source_reference,
    )
    db.commit()
    return "PROVISIONED_REQUIRES_GENUINE_GOOGLE_LOGIN"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["bootstrap", "revoke"])
    parser.add_argument("--roster", type=Path)
    parser.add_argument("--staff-key")
    parser.add_argument("--reason")
    parser.add_argument("--operator-authorized", action="store_true", required=True)
    args = parser.parse_args()
    cfg = Settings()
    if cfg.demo_enabled:
        parser.error("Institutional setup requires AKUS_DEMO_ENABLED=false")
    engine, sessions = database(cfg.database_url)
    try:
        with sessions() as db:
            if args.action == "bootstrap":
                if not args.roster:
                    parser.error("--roster must point to private approved JSON source")
                result = bootstrap(
                    db, cfg, BootstrapRoster.model_validate(json.loads(args.roster.read_text()))
                )
                print(result)
            else:
                if not args.staff_key or not args.reason or len(args.reason) < 10:
                    parser.error("Revocation needs --staff-key and a documented --reason")
                serialize_links(db)
                person = db.scalar(
                    select(Person).where(Person.staff_key == args.staff_key).with_for_update()
                )
                if person is None:
                    parser.error("Staff record not found")
                for grant in db.scalars(
                    select(AdministrativeGrant).where(
                        AdministrativeGrant.person_id == person.id,
                        AdministrativeGrant.valid_until.is_(None),
                    )
                ):
                    if grant.valid_from >= datetime.now(UTC):
                        parser.error("Future authorization requires source correction")
                    grant.valid_until = datetime.now(UTC)
                security_event(
                    db, "OPERATOR_ADMIN_REVOKED", person_id=str(person.id), reason=args.reason
                )
                db.commit()
                print("ADMIN_GRANT_REVOKED")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
