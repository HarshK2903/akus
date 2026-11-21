"""Transactional delivery to the exact assigned office. Archive contains references only."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from akus.applications.models import AcademicNotice, Application
from akus.catalog.models import AcademicEvent
from akus.models import WorkJob
from akus.people.models import OfficeAppointment

KIND = "OFFICE_INBOX"
ARCHIVED = "OFFICE_NOTICE_ARCHIVED"


def queue(db: Session, app: Application, notice: AcademicNotice, now: datetime) -> None:
    if notice.kind not in {"APPLICATION_SUBMITTED", "REVIEW_RECORDED", "REVIEW_OFFICE_ALERT"}:
        return
    if notice.kind == "REVIEW_OFFICE_ALERT":
        # The reviewer service already resolved employment, membership and office.
        # Preserve exactly those facts, including a vacancy with no addressee.
        if notice.facts.get("appointment_id"):
            db.add(WorkJob(kind=KIND, key=f"office-inbox:{notice.id}"))
        return
    office = notice.facts.get("next_office")
    if office not in {"DRC_HEAD", "HOD"}:
        return
    q = select(OfficeAppointment.id).where(
        OfficeAppointment.department_id == app.department_id,
        OfficeAppointment.office_group == office,
        OfficeAppointment.person_id != app.person_id,
        OfficeAppointment.superseded.is_(False),
        OfficeAppointment.valid_from <= now,
        or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now),
    )
    recipient = db.scalar(q)
    if recipient:
        notice.facts = notice.facts | {"recipient_office_id": str(recipient)}
        db.add(WorkJob(kind=KIND, key=f"office-inbox:{notice.id}"))


def archive(db: Session, job: WorkJob) -> None:
    notice = db.get_one(AcademicNotice, UUID(job.key.split(":")[1]))
    if db.scalar(
        select(AcademicEvent.id).where(
            AcademicEvent.entity_id == notice.id, AcademicEvent.kind == ARCHIVED
        )
    ):
        return
    if notice.kind == "REVIEW_OFFICE_ALERT" and not notice.facts.get("appointment_id"):
        return  # Pre-fix, a vacant office could leave a queued item.
    app = db.get_one(Application, notice.application_id)
    db.add(
        AcademicEvent(
            entity_id=notice.id,
            kind=ARCHIVED,
            department_id=app.department_id,
            data={
                "application_id": str(app.id),
                "recipient_office_id": (
                    notice.facts["appointment_id"]
                    if notice.kind == "REVIEW_OFFICE_ALERT"
                    else notice.facts["recipient_office_id"]
                ),
                "work_id": str(job.id),
                "channel": "IN_APP",
            },
        )
    )
