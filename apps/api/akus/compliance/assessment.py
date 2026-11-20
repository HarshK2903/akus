"""Deterministic annual and subject assessment. No quota, employment or access writes."""

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from akus.applications import participation
from akus.applications.models import Application, Reconciliation, Submission
from akus.applications.service import today
from akus.applications.workflow_models import ReviewDecision
from akus.catalog.models import Course
from akus.compliance.credentials import certified, latest
from akus.compliance.models import AssessmentSnapshot, CredentialEvent
from akus.exceptions import history
from akus.exceptions.models import (
    ArchivedObligation,
    CaseEvent,
    Departure,
    HistoricalFinding,
    SeparationSnapshot,
)
from akus.exceptions.schemas import IST
from akus.models import AcademicYear
from akus.people.models import EmploymentEpisode, OfficeAppointment, Person
from akus.sources.models import Subject, TeachingAssignment


def academic_start(day: date) -> date:
    return date(day.year - int(day.month < 7), 7, 1)


def eligibility(db: Session, app: Application, event: CredentialEvent, sub: Submission) -> str:
    if app.state == "INVALIDATED":
        return "APPROVAL_INVALIDATED"
    if db.scalar(
        select(Reconciliation.id)
        .where(
            Reconciliation.application_id == app.id,
            Reconciliation.status == "OPEN",
            Reconciliation.kind.in_(["INTEGRITY", "SOURCE_CORRECTION", "SEPARATION"]),
        )
        .limit(1)
    ):
        return "SUSPENDED_PENDING_REVIEW"
    exam = date.fromisoformat(event.facts["actual_exam_on"])
    instant = (
        datetime.fromisoformat(event.facts["actual_exam_at"])
        if event.facts.get("actual_exam_at")
        else None
    )
    episode = db.get(EmploymentEpisode, app.episode_id)
    assert episode
    if exam < episode.starts_on or exam < date.fromisoformat(sub.facts["metadata"]["starts_on"]):
        return "EXAM_BEFORE_ELIGIBLE_START"
    approved = db.scalar(
        select(ReviewDecision.recorded_at).where(
            ReviewDecision.application_id == app.id,
            ReviewDecision.stage.in_(["HOD", "ACTING_HOD"]),
            ReviewDecision.decision == "APPROVE",
        )
    )
    if not approved or app.state not in ("APPROVED", "OUTCOME_RECORDED", "SEPARATED"):
        return "INSTITUTIONAL_APPROVAL_REQUIRED"
    if episode.ends_before and episode.ends_before <= today():
        order = db.scalar(
            select(Departure).where(
                Departure.episode_id == app.episode_id,
                Departure.effective_on == episode.ends_before,
            )
        )
        if not order:
            return "SEPARATION_ORDER_PENDING"
        if history.comparison(exam, instant, order.effective_on, order.effective_at) != -1:
            return "PRE_SEPARATION_EXAM_UNCONFIRMED"
        if (
            history.comparison(
                approved.astimezone(IST).date(), approved, order.effective_on, order.effective_at
            )
            != -1
        ):
            return "PRE_SEPARATION_APPROVAL_UNCONFIRMED"
        if app.state == "SEPARATED":
            closure = db.scalar(
                select(CaseEvent)
                .join(Reconciliation)
                .where(
                    Reconciliation.application_id == app.id,
                    CaseEvent.action.in_(["Q43", "Q44", "Q45", "Q47"]),
                )
                .limit(1)
            )
            if not closure or closure.facts.get("previous_state") != "APPROVED":
                return "CLOSED_APPLICATION_APPROVAL_UNCONFIRMED"
    enrollment = participation.verified_after(db, app)
    if not enrollment:
        return "ENROLLMENT_VERIFICATION_REQUIRED"
    day = (
        enrollment.enrolled_at.astimezone(IST).date()
        if enrollment.enrolled_at
        else enrollment.enrolled_on
    )
    if not day or history.comparison(exam, instant, day, enrollment.enrolled_at) != 1:
        return "ENROLLMENT_EXAM_ORDER_UNCONFIRMED"
    if not sub.facts["declarations"].get("score_sharing_yes") or not event.facts.get(
        "verified_exam_and_score_sharing"
    ):
        return "SCORE_SHARING_UNCONFIRMED"
    return "ELIGIBLE"


def achievements(db: Session, episode_id: UUID) -> list[dict[str, Any]]:
    result = []
    for app in db.scalars(
        select(Application)
        .where(
            Application.episode_id == episode_id,
            Application.submitted_at.is_not(None),
            (
                select(CredentialEvent.id)
                .where(CredentialEvent.application_id == Application.id)
                .exists()
                | select(HistoricalFinding.id)
                .where(HistoricalFinding.application_id == Application.id)
                .exists()
            ),
        )
        .order_by(Application.id)
    ):
        event = latest(db, app.id)
        sub = db.get(Submission, app.id)
        if not sub:
            continue
        course = db.get(Course, app.course_id)
        base = {
            "application_id": str(app.id),
            "course_id": str(app.course_id),
            "course": course.title if course else str(app.course_id),
            "duration_weeks": sub.facts["metadata"]["duration_weeks"],
            "scheduled_exam_on": sub.facts["metadata"]["scheduled_exam_on"],
        }
        authoritative = certified(db, app.id)
        archive = authoritative if isinstance(authoritative, HistoricalFinding) else None
        if isinstance(authoritative, CredentialEvent):
            base["latest_submission_status"] = event.kind if event else None
            base["latest_revision"] = event.version if event else None
            event = authoritative
        if event and not archive:
            facts = event.facts
            if app.state == "SEPARATED" and event.kind == "VERIFIED":
                finding = history.report(db, app, datetime.now(UTC))["finding"]
                if finding and finding["id"] == event.id:
                    facts = facts | {
                        "subject_id": finding.get("subject_id"),
                        "relevance_basis": finding.get("relevance_basis"),
                    }
            # Rejections/revocations retain the source dates for explaining removal of credit.
            if "actual_exam_on" not in facts:
                prior = db.scalar(
                    select(CredentialEvent)
                    .where(
                        CredentialEvent.application_id == app.id,
                        CredentialEvent.version < event.version,
                        CredentialEvent.kind.in_(["VERIFIED", "ASSERTED"]),
                    )
                    .order_by(CredentialEvent.version.desc())
                    .limit(1)
                )
                facts = prior.facts if prior else event.facts
            result.append(
                base
                | {
                    k: facts.get(k)
                    for k in (
                        "actual_exam_on",
                        "issued_on",
                        "certificate_key",
                        "score_percent",
                        "subject_id",
                        "relevance_basis",
                        "actual_exam_at",
                    )
                }
                | {
                    "status": event.kind,
                    "recorded_at": event.recorded_at.isoformat(),
                    "event_id": str(event.id),
                    "eligibility": eligibility(db, app, event, sub)
                    if event.kind == "VERIFIED"
                    else "EVIDENCE_PENDING_REVIEW"
                    if event.kind == "ASSERTED"
                    else event.kind,
                }
            )
        elif archive:
            historic = archive.id
            if historic:
                item = history.report(db, app, datetime.now(UTC))["finding"]
                if item:
                    result.append(
                        base
                        | {
                            k: item.get(k)
                            for k in (
                                "actual_exam_on",
                                "issued_on",
                                "certificate_key",
                                "score_percent",
                                "subject_id",
                                "relevance_basis",
                                "eligibility",
                                "actual_exam_at",
                            )
                        }
                        | {
                            "status": "VERIFIED",
                            "event_id": str(historic),
                            "recorded_at": item["recorded_at"].isoformat(),
                        }
                    )
    return result


def annual_status(rows: list[dict[str, Any]]) -> tuple[str, list[str]]:
    selected: dict[str, str] = {}
    for r in rows:
        if r["eligibility"] != "ELIGIBLE":
            continue
        if r["duration_weeks"] >= 8:
            return "VERIFIED_FULFILLED", [r["event_id"]]
        if r["duration_weeks"] == 4:
            selected.setdefault(r["course_id"], r["event_id"])
    if len(selected) >= 2:
        return "VERIFIED_FULFILLED", list(selected.values())[:2]
    if any(r["eligibility"] == "SUSPENDED_PENDING_REVIEW" for r in rows):
        return "UNDER_INTEGRITY_REVIEW", []
    if any(r["status"] == "EXAM_VERIFIED" for r in rows):
        return "EXAM_WRITTEN_PENDING_CERTIFICATE", list(selected.values())
    if any(r["status"] == "ASSERTED" for r in rows):
        return "EXAM_REPORTED_PENDING_VERIFICATION", list(selected.values())
    return ("IN_PROGRESS" if rows else "NOT_STARTED"), list(selected.values())


def subject_rows(
    db: Session, ep: EmploymentEpisode, rows: list[dict[str, Any]], day: date
) -> list[dict[str, Any]]:
    order = db.scalar(
        select(Departure).where(Departure.episode_id == ep.id, Departure.effective_on <= day)
    )
    frozen = db.get(SeparationSnapshot, order.id) if order else None
    cutoff = min(day, ep.ends_before) if ep.ends_before else day
    firsts = {
        a.subject_id: a
        for a in reversed(
            list(
                db.scalars(
                    select(TeachingAssignment)
                    .where(
                        TeachingAssignment.episode_id == ep.id,
                        TeachingAssignment.voided.is_(False),
                        TeachingAssignment.starts_on <= cutoff,
                    )
                    .order_by(TeachingAssignment.starts_on, TeachingAssignment.id)
                )
            )
        )
    }
    records: dict[UUID, dict[str, Any]] = {
        a.subject_id: {
            "first_assignment": a.starts_on.isoformat(),
            "source_reference": a.source_reference,
            "source_id": str(a.id),
            "source_version": a.version,
        }
        for a in firsts.values()
    }
    rulings = db.scalars(
        select(ArchivedObligation).where(
            ArchivedObligation.episode_id == ep.id, ArchivedObligation.decided_on <= cutoff
        )
    )
    for ruling in rulings:
        source = records.setdefault(
            ruling.subject_id, {"first_assignment": ruling.first_assignment.isoformat()}
        )
        if (
            ruling.subject_id not in firsts
            or firsts[ruling.subject_id].starts_on != ruling.first_assignment
        ):
            source["revised_source_date"] = (
                str(firsts[ruling.subject_id].starts_on) if ruling.subject_id in firsts else None
            )
            source["source_review"] = True
            source["first_assignment"] = ruling.first_assignment.isoformat()
    if frozen:
        for item in frozen.subjects:
            sid = UUID(item["subject_id"])
            records.setdefault(sid, dict(item))["status_at_separation"] = item[
                "status_at_separation"
            ]
    result = []
    for sid, record in records.items():
        first = date.fromisoformat(record["first_assignment"])
        try:
            deadline = first.replace(year=first.year + 2).isoformat()
        except ValueError:
            deadline = None
        confirmed = history.archived_obligation(db, ep.id, sid, first, cutoff)
        subject = db.get(Subject, sid)
        matched = [r for r in rows if r.get("subject_id") == str(sid)]
        chosen = None
        state = (
            "OUTSTANDING"
            if deadline and deadline >= day.isoformat()
            else "DEADLINE_PASSED_PENDING_EVIDENCE"
        )
        for r in sorted(matched, key=lambda x: x["event_id"]):
            if r["status"] == "ASSERTED":
                state = "EXAM_REPORTED_RESULT_PENDING"
                continue
            if r["status"] != "VERIFIED":
                state = r["status"]
                continue
            state = history.silver_status(
                r["eligibility"],
                r["score_percent"],
                deadline,
                date.fromisoformat(r["actual_exam_on"]),
            )
            if state == "VERIFIED_ON_TIME":
                chosen = r["event_id"]
                break
        if record.get("source_review"):
            state = "ASSIGNMENT_SOURCE_CORRECTION_REVIEW"
        elif not deadline:
            state = "DEADLINE_POLICY_PENDING_P54"
        elif not confirmed:
            state = "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
        elif frozen and not matched:
            state = record.get("status_at_separation", "HISTORICAL_SOURCE_REVIEW")
        elif ep.ends_before and ep.ends_before <= day and not frozen:
            state = "SEPARATION_SOURCE_REVIEW"
        result.append(
            record
            | {
                "id": str(uuid5(NAMESPACE_URL, f"akus:silver:{ep.id}:{sid}")),
                "subject_id": str(sid),
                "subject": subject.name if subject else str(sid),
                "deadline": deadline,
                "monitoring": "CLOSED" if ep.ends_before and ep.ends_before <= day else "ACTIVE",
                "status": state,
                "decision_reference": confirmed.decision_reference if confirmed else None,
                "allocation": chosen if state == "VERIFIED_ON_TIME" else None,
                "candidates": matched,
            }
        )
    return sorted(result, key=lambda r: (r["first_assignment"], r["subject"]))


def assess(db: Session, ep: EmploymentEpisode) -> dict[str, Any]:
    day = today()
    person = db.get(Person, ep.person_id)
    rows = achievements(db, ep.id)
    years = list(
        db.scalars(
            select(AcademicYear)
            .where(AcademicYear.starts_on <= day, AcademicYear.ends_on >= ep.starts_on)
            .order_by(AcademicYear.starts_on.desc())
        )
    )
    annual = []
    offices = list(
        db.scalars(
            select(OfficeAppointment).where(
                OfficeAppointment.person_id == ep.person_id,
                OfficeAppointment.superseded.is_(False),
                OfficeAppointment.office.in_(["HOD", "ACTING_HOD", "PRINCIPAL"]),
            )
        )
    )
    periods = {y.starts_on: (str(y.id), y.label, y.ends_on) for y in years}
    for achievement in rows:
        if achievement.get("actual_exam_on"):
            start = academic_start(date.fromisoformat(achievement["actual_exam_on"]))
            periods.setdefault(
                start,
                (
                    start.isoformat(),
                    f"{start.year}–{str(start.year + 1)[2:]}",
                    date(start.year + 1, 6, 30),
                ),
            )
    for starts, (year_id, label, ends) in sorted(periods.items(), reverse=True):
        if ep.ends_before and starts >= ep.ends_before:
            continue
        candidates = [
            r
            for r in rows
            if r.get("actual_exam_on")
            and academic_start(date.fromisoformat(r["actual_exam_on"])) == starts
        ]
        status, allocation = annual_status(candidates)
        partial = ep.starts_on > starts or bool(ep.ends_before and ep.ends_before <= ends)
        interval_start = max(starts, ep.starts_on)
        interval_end = min(day, ends)
        obligation = "PARTIAL_YEAR_POLICY_PENDING_P55" if partial else "FACULTY_ANNUAL"
        if any(
            o.valid_from.astimezone(IST).date() < interval_start
            and (not o.valid_until or o.valid_until.astimezone(IST).date() > interval_end)
            for o in offices
        ):
            status, allocation, obligation = "NO_APPLICABLE_OBLIGATION", [], "NPTEL_EXEMPT_OFFICE"
        elif any(
            o.valid_from.astimezone(IST).date() <= interval_end
            and (not o.valid_until or o.valid_until.astimezone(IST).date() >= interval_start)
            for o in offices
        ):
            status, allocation, obligation = (
                "OFFICE_TRANSITION_POLICY_PENDING",
                [],
                "OFFICE_TRANSITION_POLICY_PENDING",
            )
        annual.append(
            {
                "id": year_id,
                "year": label,
                "starts_on": str(starts),
                "ends_on": str(ends),
                "status": status,
                "obligation": obligation,
                "allocations": allocation,
                "candidates": candidates,
            }
        )
    all_rows = list(rows)
    for older in db.scalars(
        select(EmploymentEpisode).where(
            EmploymentEpisode.person_id == ep.person_id, EmploymentEpisode.starts_on < ep.starts_on
        )
    ):
        all_rows.extend(
            r
            for r in achievements(db, older.id)
            if r["status"] == "VERIFIED" and r["eligibility"] == "ELIGIBLE" and r.get("subject_id")
        )
    silver = subject_rows(db, ep, all_rows, day)
    for row in silver:
        if row["monitoring"] == "ACTIVE" and any(
            o.valid_from.astimezone(IST).date() <= day
            and (
                not o.valid_until
                or o.valid_until.astimezone(IST).date()
                >= date.fromisoformat(row["first_assignment"])
            )
            for o in offices
        ):
            row["monitoring"] = "OFFICE_TRANSITION_POLICY_PENDING"
    return {
        "episode_id": str(ep.id),
        "person_id": str(ep.person_id),
        "name": person.display_name if person else None,
        "starts_on": str(ep.starts_on),
        "ends_before": str(ep.ends_before) if ep.ends_before else None,
        "annual": annual,
        "silver": silver,
        "policy": "V2.4/Q35–Q50",
    }


def capture(db: Session, ep: EmploymentEpisode) -> AssessmentSnapshot:
    facts = jsonable_encoder(assess(db, ep))
    digest = hashlib.sha256(
        json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    previous = db.scalar(
        select(AssessmentSnapshot)
        .where(AssessmentSnapshot.episode_id == ep.id)
        .order_by(AssessmentSnapshot.recorded_at.desc())
        .limit(1)
    )
    if previous and previous.digest == digest:
        return previous
    row = AssessmentSnapshot(
        episode_id=ep.id, digest=digest, facts=facts, recorded_at=datetime.now(UTC)
    )
    db.add(row)
    db.flush()
    return row
