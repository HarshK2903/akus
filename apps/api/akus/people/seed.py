"""Deterministic fictional source records, never inferred from demo role fields."""

from datetime import UTC, date, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from akus.people.models import (
    AdministrativeGrant,
    Department,
    DepartmentAssignment,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)


def fixture_id(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"akus.people.demo/{key}")


def seed_people(db: Session) -> None:
    for code, name in [
        ("CSE", "Computer Science · DEMO"),
        ("ECE", "Electronics · DEMO"),
        ("OPS", "Institution administration · DEMO"),
    ]:
        db.execute(
            insert(Department)
            .values(id=fixture_id(code), code=code, name=name)
            .on_conflict_do_nothing(index_elements=["code"])
        )
    fixtures = [
        ("faculty", "Mira Rao", "CSE", True, None),
        ("drc", "Arun Sen", "CSE", True, "DRC_HEAD"),
        ("hod", "Leela Iyer", "CSE", True, "HOD"),
        ("acting-hod", "Omar Das (acting HoD)", "ECE", True, "ACTING_HOD"),
        ("principal", "Dev Mehta", "OPS", False, "PRINCIPAL"),
        ("admin", "Nila Shah", "OPS", False, None),
    ]
    for key, name, dept, faculty, office in fixtures:
        person_id = fixture_id(key)
        db.execute(
            insert(Person)
            .values(
                id=person_id,
                staff_key=f"DEMO-{key.upper()}",
                display_name=name,
                demo_identity_id=uuid5(NAMESPACE_URL, f"akus.demo/{key}"),
                enabled=True,
                source_reference="LOCAL_DEMO_FIXTURE",
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        episode_id = fixture_id(f"episode/{key}")
        db.execute(
            insert(EmploymentEpisode)
            .values(
                id=episode_id,
                person_id=person_id,
                starts_on=date(2020, 7, 1),
                ends_before=None,
                is_faculty=faculty,
                source_reference="LOCAL_DEMO_FIXTURE",
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        db.execute(
            insert(DepartmentAssignment)
            .values(
                id=fixture_id(f"dept/{key}"),
                episode_id=episode_id,
                department_id=fixture_id(dept),
                starts_on=date(2020, 7, 1),
                ends_before=None,
                source_reference="LOCAL_DEMO_FIXTURE",
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        if office:
            db.execute(
                insert(OfficeAppointment)
                .values(
                    id=fixture_id(f"office/{key}"),
                    person_id=person_id,
                    office=office,
                    department_id=None if office == "PRINCIPAL" else fixture_id(dept),
                    valid_from=datetime(2025, 7, 1, tzinfo=UTC),
                    valid_until=None,
                    original_until=None,
                    source_reference="LOCAL_DEMO_FIXTURE",
                    reason="Fictional seeded appointment; not institutional evidence",
                    version=1,
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
        if key == "admin":
            db.execute(
                insert(AdministrativeGrant)
                .values(
                    id=fixture_id("admin-grant"),
                    person_id=person_id,
                    valid_from=datetime(2025, 7, 1, tzinfo=UTC),
                    valid_until=None,
                    source_reference="LOCAL_DEMO_FIXTURE",
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
    # Historical source records have no demo login mapping and confer no access.
    histories: list[tuple[str, str, list[tuple[date, date | None]]]] = [
        ("rehired", "Tara Bose", [(date(2019, 7, 1), date(2022, 3, 1)), (date(2025, 7, 1), None)]),
        ("separated", "Ravi Nair", [(date(2018, 7, 1), date(2023, 6, 1))]),
    ]
    for key, name, periods in histories:
        db.execute(
            insert(Person)
            .values(
                id=fixture_id(key),
                staff_key=f"DEMO-{key.upper()}",
                display_name=name,
                enabled=True,
                source_reference="LOCAL_DEMO_FIXTURE",
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        for n, (start, end) in enumerate(periods):
            episode_id = fixture_id(f"episode/{key}/{n}")
            db.execute(
                insert(EmploymentEpisode)
                .values(
                    id=episode_id,
                    person_id=fixture_id(key),
                    starts_on=start,
                    ends_before=end,
                    is_faculty=True,
                    source_reference="LOCAL_DEMO_FIXTURE",
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
            db.execute(
                insert(DepartmentAssignment)
                .values(
                    id=fixture_id(f"dept/{key}/{n}"),
                    episode_id=episode_id,
                    department_id=fixture_id("CSE"),
                    starts_on=start,
                    ends_before=end,
                    source_reference="LOCAL_DEMO_FIXTURE",
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
