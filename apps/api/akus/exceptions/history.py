"""Q41/Q42 frozen subjects and Q48–50 retrospective certificate findings."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import participation
from akus.applications import service as apps
from akus.applications.models import AcademicNotice, Application, Reconciliation, Submission
from akus.applications.workflow_models import ReviewDecision
from akus.catalog import common
from akus.catalog.models import Offering
from akus.catalog.service import snapshot as accepted_snapshot
from akus.exceptions import service
from akus.exceptions.models import (
    ArchivedObligation,
    CaseEvent,
    Departure,
    HistoricalFinding,
    HistoricalMandate,
    SeparationSnapshot,
)
from akus.exceptions.schemas import IST, CertificateProof, SubjectProof
from akus.models import AcademicYear
from akus.people.models import EmploymentEpisode
from akus.people.schemas import CommandResult


def authorized(
    db: Session, actor: Actor, case: Reconciliation, app: Application, purpose: str = "CERTIFICATE"
) -> HistoricalMandate | None:
    if actor.person.id == app.person_id:
        return None
    now = datetime.now(UTC)
    return db.scalar(
        select(HistoricalMandate)
        .where(
            HistoricalMandate.case_id == case.id,
            HistoricalMandate.purpose == purpose,
            HistoricalMandate.reviewer_id == actor.person.id,
            HistoricalMandate.valid_from <= now,
            HistoricalMandate.valid_until > now,
            HistoricalMandate.revoked_at.is_(None),
        )
        .order_by(HistoricalMandate.valid_from.desc(), HistoricalMandate.id)
        .with_for_update(read=True)
        .limit(1)
    )


def comparison(
    day: date, instant: datetime | None, other_day: date, other_at: datetime | None
) -> int | None:
    if day != other_day:
        return 1 if day > other_day else -1
    if instant and other_at:
        return (instant > other_at) - (instant < other_at)
    return None


def check_closure_source(
    db: Session, app: Application, offering: Offering, case_id: UUID
) -> CaseEvent:
    closure = db.scalar(
        select(CaseEvent).where(
            CaseEvent.case_id == case_id, CaseEvent.action.in_(["Q43", "Q44", "Q45", "Q47"])
        )
    )
    edition = accepted_snapshot(db, offering)
    episode = db.get(EmploymentEpisode, app.episode_id)
    if (
        not closure
        or not episode
        or not edition
        or not episode.ends_before
        or str(episode.ends_before) != closure.facts["effective_on"]
        or edition.metadata_json.get("starts_on") != closure.facts.get("starts_on")
    ):
        raise HTTPException(423, "CLOSURE_SOURCE_CORRECTION_REVIEW_REQUIRED")
    return closure


def archived_obligation(
    db: Session, episode_id: UUID, subject_id: UUID, first: date, departure: date
) -> ArchivedObligation | None:
    return db.scalar(
        select(ArchivedObligation).where(
            ArchivedObligation.episode_id == episode_id,
            ArchivedObligation.subject_id == subject_id,
            ArchivedObligation.first_assignment == first,
            ArchivedObligation.decided_on <= departure,
        )
    )


def silver_status(eligibility: str, score: float, deadline: str | None, exam: date) -> str:
    if eligibility != "ELIGIBLE":
        return "PARTICIPATION_INELIGIBLE"
    if score < 75:
        return "BELOW_SILVER_THRESHOLD"
    if not deadline:
        return "DEADLINE_POLICY_PENDING"
    return "VERIFIED_ON_TIME" if exam <= date.fromisoformat(deadline) else "EXAM_AFTER_DEADLINE"


def record(
    db: Session, actor: Actor, key: UUID, cid: UUID, body: CertificateProof
) -> CommandResult:
    service.exclusive(db)
    actor = common.refresh(db, actor, key)
    case = db.get(Reconciliation, cid)
    if not case or case.kind != "SEPARATION":
        raise HTTPException(404, "SEPARATION_CASE_REQUIRED")
    app, offering = apps.lock_application(db, case.application_id)
    grant = authorized(db, actor, case, app)
    if not grant or (body.subject_id and grant.subject_id != body.subject_id):
        raise HTTPException(403, "CERTIFICATE_OR_RELEVANCE_AUTHORITY_POLICY_PENDING")
    operation = f"HISTORICAL_CERTIFICATE:{cid}"
    if result := common.replay(db, actor, key, operation, body):
        return result
    order = service.active_order(db, app)
    if not order or case.status != "RESOLVED" or app.state != "SEPARATED":
        raise HTTPException(423, "CLOSED_SEPARATION_REQUIRED")
    snapshot = db.get(SeparationSnapshot, order.id)
    closure = check_closure_source(db, app, offering, cid)
    submission = db.get(Submission, app.id)
    if not snapshot or not closure or not submission:
        raise HTTPException(423, "SEPARATION_HISTORY_REQUIRED")
    if db.scalar(
        select(Reconciliation.id)
        .where(
            Reconciliation.application_id == app.id,
            Reconciliation.status == "OPEN",
            Reconciliation.kind.in_(["INTEGRITY", "SOURCE_CORRECTION"]),
        )
        .limit(1)
    ):
        raise HTTPException(423, "UNRESOLVED_EVIDENCE_REVIEW")
    if db.scalar(select(HistoricalFinding.id).where(HistoricalFinding.application_id == app.id)):
        raise HTTPException(409, "CERTIFICATE_ALREADY_ASSESSED")
    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.starts_on <= body.actual_exam_on,
            AcademicYear.ends_on >= body.actual_exam_on,
        )
    )
    subject = next((s for s in snapshot.subjects if s["subject_id"] == str(body.subject_id)), None)
    if body.subject_id and not subject:
        raise HTTPException(409, "SUBJECT_OUTSIDE_CLOSED_EPISODE")
    evidence = participation.verified_after(db, app)
    sep_order = comparison(
        body.actual_exam_on, body.actual_exam_at, order.effective_on, order.effective_at
    )
    enrolled_order = None
    if evidence:
        en_day = (
            evidence.enrolled_at.astimezone(IST).date()
            if evidence.enrolled_at
            else evidence.enrolled_on
        )
        assert en_day
        enrolled_order = comparison(
            body.actual_exam_on, body.actual_exam_at, en_day, evidence.enrolled_at
        )
    approval = db.scalar(
        select(ReviewDecision.recorded_at).where(
            ReviewDecision.application_id == app.id,
            ReviewDecision.stage.in_(["HOD", "ACTING_HOD"]),
            ReviewDecision.decision == "APPROVE",
        )
    )
    approval_order = (
        comparison(
            approval.astimezone(IST).date(), approval, order.effective_on, order.effective_at
        )
        if approval
        else None
    )
    if sep_order != -1:
        eligibility = (
            "SEPARATION_ORDER_UNCERTAIN" if sep_order is None else "EXAM_NOT_BEFORE_SEPARATION"
        )
    elif (
        enrolled_order != 1 or approval_order != -1 or closure.facts["previous_state"] != "APPROVED"
    ):
        eligibility = "APPROVAL_OR_ENROLLMENT_CHRONOLOGY_UNCONFIRMED"
    elif body.actual_exam_on < date.fromisoformat(closure.facts["starts_on"]):
        eligibility = "EXAM_PRECEDES_COMMENCEMENT"
    else:
        eligibility = "ELIGIBLE"
    deadline = subject["deadline"] if subject else None
    silver = (
        silver_status(eligibility, body.score_percent, deadline, body.actual_exam_on)
        if subject
        else "RELEVANCE_UNASSESSED"
    )
    accepted = (
        archived_obligation(
            db,
            app.episode_id,
            UUID(subject["subject_id"]),
            date.fromisoformat(subject["first_assignment"]),
            order.effective_on,
        )
        if subject
        else None
    )
    if silver == "VERIFIED_ON_TIME" and not accepted:
        silver = "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
    facts = body.model_dump(mode="json") | {
        "archived_obligation_id": str(accepted.id) if accepted else None,
        "departure_id": str(order.id),
        "closure_event": str(closure.id),
        "reviewer_id": str(actor.person.id),
        "designation": grant.basis,
        "eligibility": eligibility,
        "academic_year": year.label if year else None,
        "course_id": str(app.course_id),
        "duration_weeks": submission.facts["metadata"]["duration_weeks"],
        "enrollment_finding_id": str(evidence.id) if evidence else None,
        "subject_deadline": deadline,
        "silver": silver,
    }
    finding = HistoricalFinding(
        id=uuid4(),
        application_id=app.id,
        mandate_id=grant.id,
        certificate_key=body.certificate_key,
        recorded_at=datetime.now(UTC),
        facts=facts,
    )
    if db.scalar(
        select(HistoricalFinding.id).where(
            HistoricalFinding.certificate_key == body.certificate_key
        )
    ):
        raise HTTPException(409, "CERTIFICATE_ALREADY_LINKED")
    db.add(finding)
    db.flush()
    service.append(db, case, "HISTORICAL_CERTIFICATE_VERIFIED", facts, actor)
    apps.notice(
        db,
        app,
        "HISTORICAL_CERTIFICATE",
        {"finding_id": str(finding.id), "eligibility": eligibility},
    )
    for later in db.scalars(
        select(Application)
        .where(
            Application.person_id == app.person_id,
            Application.course_id == app.course_id,
            Application.submitted_at > submission.submitted_at,
            Application.state.in_(["APPROVED", "OUTCOME_RECORDED"]),
        )
        .order_by(Application.id)
    ):
        apps.case(
            db,
            later,
            "INTEGRITY",
            "PRIOR_CERTIFICATE_AUTHORITY_POLICY_PENDING",
            {"historical_finding_id": str(finding.id), "recognition": "SUSPENDED"},
        )
    return common.finish(db, actor, key, operation, body, finding.id, facts, app.department_id)


def report(db: Session, app: Application, as_of: datetime) -> dict[str, Any]:
    return episode_report(db, app.episode_id, app.id, as_of)


def annual_standing(eligible: list[dict[str, Any]]) -> dict[str, str]:
    years: dict[str, dict[str, Any]] = {}
    for f in eligible:
        if f["academic_year"]:
            bucket = years.setdefault(
                f["academic_year"], {"courses_four": set(), "long_course": False}
            )
            if f["duration_weeks"] >= 8:
                bucket["long_course"] = True
            if f["duration_weeks"] == 4:
                bucket["courses_four"].add(f["course_id"])
    return {
        year: "VERIFIED_FULFILLED"
        if b["long_course"] or len(b["courses_four"]) >= 2
        else "INSUFFICIENT_QUALIFYING_COURSES"
        for year, b in years.items()
    }


def episode_report(
    db: Session, episode_id: UUID, application_id: UUID | None, as_of: datetime
) -> dict[str, Any]:
    """Reconstruct what the closed episode's records established by a knowledge cutoff."""
    if as_of.tzinfo is None or as_of > datetime.now(UTC):
        raise HTTPException(422, "VALID_HISTORICAL_INSTANT_REQUIRED")
    snapshot = db.scalar(
        select(SeparationSnapshot)
        .join(Departure)
        .where(Departure.episode_id == episode_id, SeparationSnapshot.recorded_at <= as_of)
    )
    rows = db.scalars(
        select(HistoricalFinding)
        .join(Application)
        .where(Application.episode_id == episode_id, HistoricalFinding.recorded_at <= as_of)
        .order_by(HistoricalFinding.recorded_at, HistoricalFinding.id)
    )
    eligible: list[dict[str, Any]] = []
    subjects = {s["subject_id"]: dict(s) for s in snapshot.subjects} if snapshot else {}
    own = None
    for row in rows:
        f = row.facts
        relevance = db.scalar(
            select(CaseEvent)
            .join(Reconciliation)
            .where(
                Reconciliation.application_id == row.application_id,
                CaseEvent.action == "SUBJECT_RELEVANCE_VERIFIED",
                CaseEvent.recorded_at <= as_of,
            )
            .order_by(CaseEvent.version.desc())
            .limit(1)
        )
        if relevance:
            f = (
                f
                | {
                    k: relevance.facts[k]
                    for k in (
                        "subject_id",
                        "subject_deadline",
                        "silver",
                        "relevance_basis",
                        "archived_obligation_id",
                    )
                }
                | {"relevance_recorded_at": relevance.recorded_at}
            )
        # A later correction suspends the latest assessment; earlier reports still see
        # only events that had actually been recorded by their knowledge cutoff.
        hold = False
        for kind in ("INTEGRITY", "SOURCE_CORRECTION"):
            last_notice = db.scalar(
                select(AcademicNotice)
                .where(
                    AcademicNotice.application_id == row.application_id,
                    AcademicNotice.kind.in_([kind, kind + "_RESOLVED"]),
                    AcademicNotice.created_at <= as_of,
                )
                .order_by(AcademicNotice.created_at.desc(), AcademicNotice.id.desc())
                .limit(1)
            )
            hold |= bool(last_notice and last_notice.kind == kind)
        if hold:
            f = f | {
                "eligibility": "SUSPENDED_PENDING_REVIEW",
                "silver": "SUSPENDED_PENDING_REVIEW",
            }
        if row.application_id == application_id:
            own = {"id": row.id, "recorded_at": row.recorded_at, **f}
        if f["eligibility"] != "ELIGIBLE":
            continue
        eligible.append(f)
        if f.get("subject_id") in subjects and f["silver"] == "VERIFIED_ON_TIME":
            subjects[f["subject_id"]]["reassessment"] = "VERIFIED_ON_TIME"
    return {
        "as_of": as_of,
        "snapshot_at": snapshot.recorded_at if snapshot else None,
        "annual": annual_standing(eligible),
        "subjects": list(subjects.values()),
        "finding": own,
    }


def verify_subject(
    db: Session, actor: Actor, key: UUID, cid: UUID, body: SubjectProof
) -> CommandResult:
    service.exclusive(db)
    actor = common.refresh(db, actor, key)
    c = db.get(Reconciliation, cid)
    if not c or c.kind != "SEPARATION":
        raise HTTPException(404, "CASE_NOT_FOUND")
    app, offering = apps.lock_application(db, c.application_id)
    grant = authorized(db, actor, c, app)
    if not grant or grant.subject_id != body.subject_id:
        raise HTTPException(403, "SUBJECT_RELEVANCE_AUTHORITY_POLICY_PENDING")
    operation = f"HISTORICAL_RELEVANCE:{cid}"
    if replay := common.replay(db, actor, key, operation, body):
        return replay
    check_closure_source(db, app, offering, cid)
    result = report(db, app, datetime.now(UTC))
    finding = result["finding"]
    if not finding or finding["id"] != body.finding_id or finding["eligibility"] != "ELIGIBLE":
        raise HTTPException(423, "ELIGIBLE_VERIFIED_CERTIFICATE_REQUIRED")
    if finding.get("subject_id") and not (
        finding["subject_id"] == str(body.subject_id)
        and finding["silver"] == "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
    ):
        raise HTTPException(423, "SUBJECT_ALREADY_ASSESSED_MULTIPLE_SUBJECT_POLICY_PENDING")
    subject = next((s for s in result["subjects"] if s["subject_id"] == str(body.subject_id)), None)
    if not subject:
        raise HTTPException(409, "SUBJECT_OUTSIDE_CLOSED_EPISODE")
    deadline = subject["deadline"]
    order = service.active_order(db, app)
    assert order
    accepted = archived_obligation(
        db,
        app.episode_id,
        UUID(subject["subject_id"]),
        date.fromisoformat(subject["first_assignment"]),
        order.effective_on,
    )
    if finding.get("subject_id") and not accepted:
        raise HTTPException(423, "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02")
    facts = body.model_dump(mode="json") | {
        "archived_obligation_id": str(accepted.id) if accepted else None,
        "subject_deadline": deadline,
        "mandate_id": str(grant.id),
        "designation": grant.basis,
        "silver": silver_status(
            finding["eligibility"],
            finding["score_percent"],
            deadline,
            date.fromisoformat(finding["actual_exam_on"]),
        ),
    }
    if facts["silver"] == "VERIFIED_ON_TIME" and not accepted:
        facts["silver"] = "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
    service.append(db, c, "SUBJECT_RELEVANCE_VERIFIED", facts, actor)
    apps.notice(
        db,
        app,
        "HISTORICAL_RELEVANCE",
        {"finding_id": str(body.finding_id), "silver": facts["silver"]},
    )
    return common.finish(db, actor, key, operation, body, body.finding_id, facts, app.department_id)
