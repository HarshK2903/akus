"""Idempotent fictional fixtures. Refuses non-demo environments."""

from datetime import date
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from akus.config import Settings
from akus.db import database
from akus.models import AcademicYear, DemoIdentity, WorkJob
from akus.people.seed import seed_people

FIXTURES = [
    ("faculty", "Mira Rao", "FACULTY", "Computer Science · DEMO"),
    ("drc", "Arun Sen", "DRC_HEAD", "Computer Science · DEMO"),
    ("hod", "Leela Iyer", "HOD", "Computer Science · DEMO"),
    ("principal", "Dev Mehta", "PRINCIPAL", "Institution-wide · DEMO"),
    ("admin", "Nila Shah", "ADMIN", "Reference administration · DEMO"),
    ("acting-hod", "Omar Das (acting HoD)", "HOD", "Electronics · DEMO"),
]


def seed(db: Session) -> None:
    for key, name, role, department in FIXTURES:
        db.execute(
            insert(DemoIdentity)
            .values(
                id=uuid5(NAMESPACE_URL, f"akus.demo/{key}"),
                key=key,
                name=name,
                role=role,
                department=department,
            )
            .on_conflict_do_nothing(index_elements=["key"])
        )
    for year in (2026, 2027):
        db.execute(
            insert(AcademicYear)
            .values(
                id=uuid5(NAMESPACE_URL, f"akus.demo/year/{year}"),
                label=f"{year}–{str(year + 1)[2:]}",
                starts_on=date(year, 7, 1),
                ends_on=date(year + 1, 6, 30),
                source="LOCAL_DEMO_FIXTURE",
            )
            .on_conflict_do_nothing(index_elements=["label"])
        )
    db.execute(
        insert(WorkJob)
        .values(key="foundation-demo-bootstrap-v1", kind="LOCAL_DEMO_BOOTSTRAP", state="PENDING")
        .on_conflict_do_nothing(index_elements=["key"])
    )
    seed_people(db)
    db.commit()


def main() -> None:
    settings = Settings()
    if not settings.demo_enabled:
        raise RuntimeError("Seeding requires explicit AKUS_DEMO_ENABLED=true")
    engine, factory = database(settings.database_url)
    with factory() as db:
        seed(db)
    engine.dispose()
    print(
        "LOCAL DEMO fixtures ready. Fictional source records only; no real institutional or provider facts."
    )


if __name__ == "__main__":
    main()
