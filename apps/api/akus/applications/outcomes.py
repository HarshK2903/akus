"""Q27–30 repeat eligibility; Q33 holds without inventing integrity disposition.

Rare prior-result writes take the existing source-authority gate exclusively BEFORE
any other locks. This serializes evidence corrections with admission, review, source
changes and multi-application closure without upgrading a shared lock or introducing
a canonical/application lock inversion. No network I/O occurs in the transaction.
"""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import service
from akus.applications.models import Allocation, Application, Ledger, Reconciliation
from akus.applications.outcome_models import Attempt, AttemptEvidence, OutcomeFinding
from akus.applications.outcome_schemas import AttemptWrite, OutcomeDecision
from akus.catalog import common
from akus.catalog.models import Course, Offering
from akus.catalog.service import snapshot
from akus.people.models import DepartmentAssignment, EmploymentEpisode, OfficeAppointment, Person
from akus.people.schemas import CommandResult


def subject_department(db: Session, person_id: UUID, eligible: bool = False) -> UUID | None:
    day, now = service.today(), datetime.now(UTC)
    query = (
        select(DepartmentAssignment.department_id)
        .join(EmploymentEpisode)
        .where(
            EmploymentEpisode.person_id == person_id,
            EmploymentEpisode.starts_on <= day,
            or_(EmploymentEpisode.ends_before.is_(None), EmploymentEpisode.ends_before > day),
            DepartmentAssignment.starts_on <= day,
            or_(DepartmentAssignment.ends_before.is_(None), DepartmentAssignment.ends_before > day),
        )
    )
    if eligible:
        query = query.where(EmploymentEpisode.is_faculty.is_(True))
        exempt = db.scalar(
            select(OfficeAppointment.id).where(
                OfficeAppointment.person_id == person_id,
                OfficeAppointment.superseded.is_(False),
                OfficeAppointment.office.in_(["HOD", "ACTING_HOD", "PRINCIPAL"]),
                OfficeAppointment.valid_from <= now,
                or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now),
            )
        )
        person = db.get(Person, person_id)
        if exempt or not person or not person.enabled:
            return None
    return db.scalar(query)


def can_read(db: Session, actor: Actor, attempt: Attempt) -> None:
    if actor.person.id == attempt.person_id:
        return
    dept = subject_department(db, attempt.person_id)
    if any(o.department_id == dept and o.office in {"HOD", "ACTING_HOD"} for o in actor.offices):
        return
    raise HTTPException(403, "ATTEMPT_ACCESS_DENIED")


def latest_evidence(db: Session, aid: UUID) -> AttemptEvidence | None:
    return db.scalar(
        select(AttemptEvidence)
        .where(AttemptEvidence.attempt_id == aid)
        .order_by(AttemptEvidence.version.desc())
        .limit(1)
    )


def latest_finding(db: Session, aid: UUID) -> OutcomeFinding | None:
    return db.scalar(
        select(OutcomeFinding)
        .where(OutcomeFinding.attempt_id == aid)
        .order_by(OutcomeFinding.version.desc())
        .limit(1)
    )


def certificate_known(db: Session, aid: UUID) -> bool:
    # A later assertion or no-cert finding cannot silently revoke a verified certificate.
    return (
        db.scalar(
            select(OutcomeFinding.id)
            .where(OutcomeFinding.attempt_id == aid, OutcomeFinding.outcome == "VALID_CERT")
            .limit(1)
        )
        is not None
    )


def conclusive_no_cert(db: Session, attempt: Attempt) -> bool:
    evidence, finding = latest_evidence(db, attempt.id), latest_finding(db, attempt.id)
    return bool(
        evidence
        and finding
        and evidence.id == finding.evidence_id
        and finding.outcome == "NO_VALID_CERT"
        and not certificate_known(db, attempt.id)
    )


def assert_repeat_eligible(db: Session, app: Application) -> dict[UUID, Attempt]:
    from akus.exceptions.models import HistoricalFinding

    if db.scalar(
        select(HistoricalFinding.id)
        .join(Application)
        .where(
            Application.person_id == app.person_id,
            Application.course_id == app.course_id,
            Application.id != app.id,
        )
        .limit(1)
    ):
        raise HTTPException(409, "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28")
    attempts = list(
        db.scalars(
            select(Attempt).where(
                Attempt.person_id == app.person_id, Attempt.course_id == app.course_id
            )
        )
    )
    for attempt in attempts:
        if certificate_known(db, attempt.id):
            raise HTTPException(409, "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28")
        if (
            attempt.offering_id == app.offering_id
            and app.state == "DRAFT"
            and conclusive_no_cert(db, attempt)
        ):
            raise HTTPException(409, "CONCLUDED_ATTEMPT_REQUIRES_DIFFERENT_OFFERING")
        # Evidence for the *current* attempt doesn't make that application a repeat.
        if attempt.offering_id != app.offering_id or app.state == "DRAFT":
            if not conclusive_no_cert(db, attempt):
                raise HTTPException(423, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29")
    return {a.offering_id: a for a in attempts}


def write(db: Session, actor: Actor, key: UUID, body: AttemptWrite) -> CommandResult:
    db.execute(text("SELECT pg_advisory_xact_lock(8210402)"))
    actor = common.refresh(db, actor, key)
    common.require_applicant(actor)
    op = f"PRIOR_ATTEMPT_EVIDENCE:{body.offering_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    offering = db.get(Offering, body.offering_id)
    if not offering:
        raise HTTPException(404, "OFFERING_NOT_FOUND")
    attempt = db.scalar(
        select(Attempt).where(
            Attempt.person_id == actor.person.id, Attempt.offering_id == offering.id
        )
    )
    previous = latest_evidence(db, attempt.id) if attempt else None
    if body.expected_version != (previous.version if previous else 0):
        raise HTTPException(409, "VERSION_CONFLICT")
    if not attempt:
        attempt = Attempt(
            id=uuid4(),
            person_id=actor.person.id,
            course_id=offering.course_id,
            offering_id=offering.id,
            department_id=actor.department.id,
        )
        db.add(attempt)
        db.flush()
    evidence = AttemptEvidence(
        id=uuid4(),
        attempt_id=attempt.id,
        actor_id=actor.person.id,
        version=body.expected_version + 1,
        **body.model_dump(exclude={"offering_id", "expected_version"}),
    )
    db.add(evidence)
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        attempt.id,
        {"evidence_id": str(evidence.id), "verification": "UNVERIFIED_ASSERTION"},
        actor.department.id,
    )


def decide(db: Session, actor: Actor, key: UUID, aid: UUID, body: OutcomeDecision) -> CommandResult:
    db.execute(text("SELECT pg_advisory_xact_lock(8210402)"))
    actor = common.refresh(db, actor, key)
    attempt = db.get(Attempt, aid)
    if not attempt:
        raise HTTPException(404, "ATTEMPT_NOT_FOUND")
    dept = subject_department(db, attempt.person_id, eligible=True)
    if not dept:
        raise HTTPException(423, "PRIOR_OUTCOME_APPLICANT_AUTHORITY_PENDING")
    office = common.require_hod(actor, dept)
    if attempt.person_id == actor.person.id:
        raise HTTPException(403, "SELF_VERIFICATION_PROHIBITED")
    op = f"PRIOR_OUTCOME_DECIDED:{aid}"
    if result := common.replay(db, actor, key, op, body):
        return result
    evidence, previous = latest_evidence(db, aid), latest_finding(db, aid)
    if (
        not evidence
        or evidence.id != body.evidence_id
        or body.expected_version != (previous.version if previous else 0)
    ):
        raise HTTPException(409, "OUTCOME_EVIDENCE_CHANGED")
    if previous and body.observed_at < previous.observed_at:
        raise HTTPException(409, "STALE_OUTCOME_EVIDENCE")
    if certificate_known(db, aid) and body.outcome == "NO_VALID_CERT":
        raise HTTPException(423, "CERTIFICATE_REVOCATION_AUTHORITY_POLICY_PENDING")
    offering = db.get(Offering, attempt.offering_id)
    accepted = snapshot(db, offering) if offering else None
    starts_on = accepted.metadata_json.get("starts_on") if accepted else None
    if body.concluded_on and starts_on and body.concluded_on < date.fromisoformat(starts_on):
        raise HTTPException(423, "OUTCOME_PRECEDES_COURSE_START_RECONCILIATION_REQUIRED")
    finding = OutcomeFinding(
        id=uuid4(),
        attempt_id=aid,
        version=body.expected_version + 1,
        actor_id=actor.person.id,
        office_id=office.id,
        **body.model_dump(
            exclude={
                "expected_version",
                "independently_authenticated_person_and_run",
                "conclusive_official_result",
            }
        ),
    )
    db.add(finding)
    db.flush()
    affected = []
    # Exclusive gate already prevents new submissions/corrections during this pass.
    applications = list(
        db.scalars(
            select(Application)
            .where(
                Application.person_id == attempt.person_id,
                Application.course_id == attempt.course_id,
                Application.state.in_(["APPROVED", "OUTCOME_RECORDED"]),
            )
            .order_by(Application.offering_id, Application.id)
        )
    )
    for candidate in applications:
        app, _ = service.lock_application(db, candidate.id)
        if app.offering_id != attempt.offering_id:
            if body.outcome == "VALID_CERT":
                corrected = db.scalar(
                    select(OutcomeFinding.id)
                    .where(
                        OutcomeFinding.attempt_id == aid,
                        OutcomeFinding.outcome == "NO_VALID_CERT",
                        OutcomeFinding.recorded_at < app.submitted_at,
                    )
                    .limit(1)
                )
                if not corrected and app.state == "OUTCOME_RECORDED":
                    continue
                service.case(
                    db,
                    app,
                    "INTEGRITY",
                    "Q33_AUTHORITY_POLICY_PENDING"
                    if corrected
                    else "PRIOR_CERTIFICATE_AUTHORITY_POLICY_PENDING",
                    {
                        "attempt_id": str(aid),
                        "finding_id": str(finding.id),
                        "recognition": "SUSPENDED",
                        "quota": "RETAIN_CURRENT_COUNT",
                        "misconduct": "NOT_INFERRED",
                    },
                )
                affected.append(str(app.id))
            continue
        if app.state != "APPROVED" or body.outcome == "UNRESOLVED":
            continue
        if db.scalar(
            select(Reconciliation.id).where(
                Reconciliation.application_id == app.id,
                Reconciliation.kind == "INTEGRITY",
                Reconciliation.status == "OPEN",
            )
        ):
            continue
        allocation = db.get(Allocation, app.id)
        assert allocation and allocation.state == "CONFIRMED"
        # A concluded run ceases to be active; the historic counted seat stays counted.
        allocation.state, allocation.version = "RETAINED", allocation.version + 1
        app.state, app.next_office, app.version = "OUTCOME_RECORDED", None, app.version + 1
        db.add(
            Ledger(
                id=uuid4(),
                movement_id=uuid4(),
                application_id=app.id,
                pool_id=allocation.pool_id,
                delta=0,
                kind="OUTCOME_RETAIN",
                snapshot_id=allocation.schedule_snapshot_id,
                personal_schedule_id=allocation.personal_schedule_id,
                actor_id=actor.person.id,
            )
        )
        service.notice(
            db,
            app,
            "OUTCOME_RECORDED",
            {
                "attempt_id": str(aid),
                "finding_id": str(finding.id),
                "outcome": body.outcome,
                "quota": "RETAIN_CURRENT_COUNT",
                "compliance": "NOT_ASSESSED",
            },
        )
        affected.append(str(app.id))
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        aid,
        body.model_dump(mode="json")
        | {
            "finding_id": str(finding.id),
            "office_id": str(office.id),
            "affected_applications": affected,
            "compliance": "NOT_ASSESSED",
        },
        dept,
    )


def view(db: Session, actor: Actor, attempt: Attempt, detail: bool = True) -> dict[str, Any]:
    can_read(db, actor, attempt)
    evidence, finding = latest_evidence(db, attempt.id), latest_finding(db, attempt.id)
    course, offering, person = (
        db.get(Course, attempt.course_id),
        db.get(Offering, attempt.offering_id),
        db.get(Person, attempt.person_id),
    )
    dept = subject_department(db, attempt.person_id, eligible=True)

    def row(r: AttemptEvidence | OutcomeFinding) -> dict[str, Any]:
        keys = [
            "id",
            "version",
            "actor_id",
            "source_reference",
            "document_digest",
            "observed_at",
            "reason",
            "recorded_at",
        ]
        keys += (
            ["outcome", "office_id", "concluded_on", "evidence_id"]
            if isinstance(r, OutcomeFinding)
            else ["asserted_outcome"]
        )
        return {k: getattr(r, k) for k in keys}

    known = certificate_known(db, attempt.id)
    result: dict[str, Any] = {
        "id": attempt.id,
        "person_id": attempt.person_id,
        "applicant": person.display_name if person else None,
        "course_id": attempt.course_id,
        "course": course.title if course else None,
        "offering_id": attempt.offering_id,
        "provider_id": offering.provider_id if offering else None,
        "own": attempt.person_id == actor.person.id,
        "can_decide": actor.person.id != attempt.person_id
        and dept is not None
        and any(
            o.department_id == dept and o.office in {"HOD", "ACTING_HOD"} for o in actor.offices
        ),
        "evidence_version": evidence.version if evidence else 0,
        "finding_version": finding.version if finding else 0,
        "eligibility": "REPEAT_PROHIBITED"
        if known
        else "NO_CERT_VERIFIED"
        if conclusive_no_cert(db, attempt)
        else "OUTCOME_PENDING",
    }
    if not detail:
        return result
    return result | {
        "evidence": [
            row(r)
            for r in db.scalars(
                select(AttemptEvidence)
                .where(AttemptEvidence.attempt_id == attempt.id)
                .order_by(AttemptEvidence.version.desc())
            )
        ],
        "findings": [
            row(r)
            for r in db.scalars(
                select(OutcomeFinding)
                .where(OutcomeFinding.attempt_id == attempt.id)
                .order_by(OutcomeFinding.version.desc())
            )
        ],
        "storage": "OFFICIAL_ARCHIVE_REFERENCE_ONLY",
        "compliance": "NOT_ASSESSED",
    }
