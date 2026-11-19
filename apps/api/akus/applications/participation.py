"""Person-specific enrollment assertions, HoD verification and Q04 decisions.

Material remains in the referenced official archive. No provider authentication or
binary-file scan is implied by storing a reference and its SHA-256.
"""

from datetime import datetime, time, timedelta
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import service
from akus.applications.models import Application, Reconciliation
from akus.applications.participation_schemas import (
    DecideWithdrawal,
    EnrollmentProof,
    EnrollmentVerify,
    RequestWithdrawal,
)
from akus.applications.workflow_models import (
    EnrollmentClaim,
    EnrollmentFinding,
    WithdrawalDecision,
    WithdrawalRequest,
)
from akus.catalog import common
from akus.config import Settings
from akus.people.schemas import CommandResult


def claim_current(db: Session, app_id: UUID) -> EnrollmentClaim | None:
    return db.scalar(
        select(EnrollmentClaim)
        .where(EnrollmentClaim.application_id == app_id)
        .order_by(EnrollmentClaim.version.desc())
        .limit(1)
    )


def finding_current(db: Session, app_id: UUID) -> EnrollmentFinding | None:
    return db.scalar(
        select(EnrollmentFinding)
        .where(EnrollmentFinding.application_id == app_id)
        .order_by(EnrollmentFinding.version.desc())
        .limit(1)
    )


def known_enrollment(db: Session, app: Application) -> bool:
    return (
        db.scalar(
            select(EnrollmentClaim.id)
            .join(Application)
            .where(
                Application.person_id == app.person_id, Application.offering_id == app.offering_id
            )
            .limit(1)
        )
        is not None
    )


def chronology(app: Application, fact: EnrollmentFinding) -> str:
    if not app.submitted_at:
        return "BEFORE_VALID_SUBMISSION"
    if fact.enrolled_at:
        return (
            "AFTER_SUBMISSION" if fact.enrolled_at > app.submitted_at else "BEFORE_VALID_SUBMISSION"
        )
    assert fact.enrolled_on
    start = datetime.combine(fact.enrolled_on, time.min, ZoneInfo("Asia/Kolkata"))
    if start > app.submitted_at:
        return "AFTER_SUBMISSION"
    if start + timedelta(days=1) <= app.submitted_at:
        return "BEFORE_VALID_SUBMISSION"
    return "INDETERMINATE_SAME_DAY"


def verified_after(db: Session, app: Application) -> EnrollmentFinding | None:
    claim, finding = claim_current(db, app.id), finding_current(db, app.id)
    if (
        claim
        and finding
        and finding.claim_id == claim.id
        and finding.outcome == "VERIFIED"
        and chronology(app, finding) == "AFTER_SUBMISSION"
    ):
        return finding
    return None


def assert_review_chronology(db: Session, app: Application) -> None:
    if db.scalar(
        select(Reconciliation.id).where(
            Reconciliation.application_id == app.id,
            Reconciliation.kind == "INTEGRITY",
            Reconciliation.status == "OPEN",
        )
    ):
        raise HTTPException(423, "INTEGRITY_AUTHORITY_POLICY_PENDING")
    if known_enrollment(db, app) and not verified_after(db, app):
        raise HTTPException(423, "VERIFIED_ENROLLMENT_CHRONOLOGY_REQUIRED")


def claim(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: EnrollmentProof
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, _ = service.lock_application(db, app_id, actor)
    common.require_applicant(actor)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "OWN_APPLICATION_REQUIRED")
    op = f"ENROLLMENT_CLAIMED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    if app.state not in {"DRAFT", "UNDER_REVIEW", "APPROVED"}:
        raise HTTPException(409, "LIVE_APPLICATION_REQUIRED")
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
        {"key": f"canonical:{app.person_id}:{app.course_id}"},
    )
    prior = claim_current(db, app.id)
    if body.expected_version != (prior.version if prior else 0):
        raise HTTPException(409, "VERSION_CONFLICT")
    record = EnrollmentClaim(
        id=uuid4(),
        application_id=app.id,
        actor_id=actor.person.id,
        version=body.expected_version + 1,
        **body.model_dump(exclude={"expected_version"}),
    )
    db.add(record)
    if app.state != "DRAFT":
        service.case(
            db,
            app,
            "ENROLLMENT",
            "HOD_ENROLLMENT_VERIFICATION_PENDING",
            {"claim_id": str(record.id)},
        )
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        {"claim_id": str(record.id), "verification": "UNVERIFIED_ASSERTION"},
        app.department_id,
    )


def verify(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: EnrollmentVerify
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, _ = service.lock_application(db, app_id, actor)
    office = common.require_hod(actor, app.department_id)
    if app.person_id == actor.person.id:
        raise HTTPException(403, "SELF_VERIFICATION_PROHIBITED")
    op = f"ENROLLMENT_VERIFIED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    if app.state not in {"UNDER_REVIEW", "APPROVED"} or not service.applicant_still_eligible(
        db, app
    ):
        raise HTTPException(423, "LIVE_ELIGIBLE_APPLICATION_REQUIRED")
    latest, prior = claim_current(db, app.id), finding_current(db, app.id)
    if (
        not latest
        or latest.id != body.claim_id
        or body.expected_version != (prior.version if prior else 0)
    ):
        raise HTTPException(409, "ENROLLMENT_EVIDENCE_CHANGED")
    if prior and body.observed_at < prior.observed_at:
        raise HTTPException(409, "STALE_ENROLLMENT_EVIDENCE")
    finding = EnrollmentFinding(
        id=uuid4(),
        application_id=app.id,
        actor_id=actor.person.id,
        office_id=office.id,
        version=body.expected_version + 1,
        **body.model_dump(exclude={"expected_version", "independently_authenticated"}),
    )
    db.add(finding)
    order = chronology(app, finding)
    if body.outcome == "VERIFIED" and order == "AFTER_SUBMISSION":
        service.resolve_case(db, app, "ENROLLMENT", "HOD_VERIFIED_SUBMISSION_FIRST")
    else:
        service.case(
            db,
            app,
            "ENROLLMENT",
            "ENROLLMENT_CHRONOLOGY_REVIEW_REQUIRED",
            {"finding_id": str(finding.id), "chronology": order, "outcome": body.outcome},
        )
    if (
        app.state == "APPROVED"
        and body.outcome == "VERIFIED"
        and order == "BEFORE_VALID_SUBMISSION"
    ):
        service.case(
            db,
            app,
            "INTEGRITY",
            "Q22_AUTHORITY_POLICY_PENDING",
            {
                "finding_id": str(finding.id),
                "recognition": "SUSPENDED",
                "quota": "RETAIN_CURRENT_COUNT",
            },
        )
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        body.model_dump(mode="json")
        | {
            "finding_id": str(finding.id),
            "office_id": str(office.id),
            "chronology": order,
            "verification": "MANUAL_HOD_AUTHENTICATED",
        },
        app.department_id,
    )


def pending_withdrawal(db: Session, app_id: UUID) -> WithdrawalRequest | None:
    return db.scalar(
        select(WithdrawalRequest)
        .where(
            WithdrawalRequest.application_id == app_id,
            ~WithdrawalRequest.id.in_(select(WithdrawalDecision.request_id)),
        )
        .order_by(WithdrawalRequest.recorded_at.desc())
        .limit(1)
    )


def request_withdrawal(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: RequestWithdrawal, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, offering = service.lock_application(db, app_id, actor)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "OWN_APPLICATION_REQUIRED")
    common.require_applicant(actor)
    op = f"WITHDRAWAL_REQUESTED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    service.check_version(app, body.expected_version)
    if app.state not in {"UNDER_REVIEW", "APPROVED"}:
        raise HTTPException(409, "ACTIVE_APPLICATION_REQUIRED")
    source = service.verified_commencement(db, offering, cfg)
    if service.today().isoformat() >= source.metadata_json["starts_on"]:
        raise HTTPException(423, "POST_START_WITHDRAWAL_RETAINS_QUOTA_Q05")
    if not known_enrollment(db, app):
        raise HTTPException(423, "ENROLLMENT_EVIDENCE_REQUIRED_FOR_Q04")
    if pending_withdrawal(db, app.id):
        raise HTTPException(409, "WITHDRAWAL_REQUEST_ALREADY_OPEN")
    record = WithdrawalRequest(
        id=uuid4(),
        application_id=app.id,
        actor_id=actor.person.id,
        source_reference=body.source_reference,
        reason=body.reason,
    )
    db.add(record)
    service.case(
        db, app, "WITHDRAWAL", "HOD_WITHDRAWAL_DECISION_PENDING_Q04", {"request_id": str(record.id)}
    )
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        {"request_id": str(record.id), "quota": "RETAIN_CURRENT_COUNT"},
        app.department_id,
    )


def decide_withdrawal(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: DecideWithdrawal, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    app, offering = service.lock_application(db, app_id, actor)
    office = common.require_hod(actor, app.department_id)
    if actor.person.id == app.person_id:
        raise HTTPException(403, "SELF_REVIEW_PROHIBITED")
    op = f"WITHDRAWAL_DECIDED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    service.check_version(app, body.expected_version)
    pending = pending_withdrawal(db, app.id)
    if (
        app.state not in {"UNDER_REVIEW", "APPROVED"}
        or not pending
        or pending.id != body.request_id
    ):
        raise HTTPException(409, "CURRENT_WITHDRAWAL_REQUEST_REQUIRED")
    if not service.applicant_still_eligible(db, app):
        raise HTTPException(423, "APPLICANT_SOURCE_CHANGE_POLICY_PENDING")
    finding = verified_after(db, app)
    facts = body.model_dump(mode="json")
    if body.decision == "AUTHORIZE":
        assert_review_chronology(db, app)
        if not finding:
            raise HTTPException(423, "VERIFIED_ENROLLMENT_REQUIRED_Q04")
        source = service.verified_commencement(db, offering, cfg)
        if service.today().isoformat() >= source.metadata_json["starts_on"]:
            raise HTTPException(423, "POST_START_WITHDRAWAL_RETAINS_QUOTA_Q05")
        facts |= {
            "commencement_snapshot_id": str(source.id),
            "starts_on": source.metadata_json["starts_on"],
            "enrollment_finding_id": str(finding.id),
        }
        service.release(db, app, actor, "HOD_WITHDRAW_RELEASE")
        app.state, app.next_office, app.version = "WITHDRAWN", None, app.version + 1
    service.resolve_case(db, app, "WITHDRAWAL", "HOD_WITHDRAWAL_" + body.decision)
    db.add(
        WithdrawalDecision(
            id=uuid4(),
            request_id=pending.id,
            actor_id=actor.person.id,
            office_id=office.id,
            decision=body.decision,
            finding_id=finding.id if finding else None,
            facts=facts,
        )
    )
    return common.finish(
        db, actor, key, op, body, app.id, facts | {"office_id": str(office.id)}, app.department_id
    )


def view(db: Session, app: Application) -> dict[str, Any]:
    def evidence(row: EnrollmentClaim | EnrollmentFinding) -> dict[str, Any]:
        result = {
            key: getattr(row, key)
            for key in (
                "id",
                "version",
                "enrolled_at",
                "enrolled_on",
                "source_reference",
                "document_digest",
                "observed_at",
                "recorded_at",
                "reason",
                "actor_id",
            )
        }
        if isinstance(row, EnrollmentFinding):
            result |= {
                "claim_id": row.claim_id,
                "office_id": row.office_id,
                "outcome": row.outcome,
                "chronology": chronology(app, row),
            }
        return result

    claim, finding, pending = (
        claim_current(db, app.id),
        finding_current(db, app.id),
        pending_withdrawal(db, app.id),
    )
    return {
        "claim_version": claim.version if claim else 0,
        "finding_version": finding.version if finding else 0,
        "claims": [
            evidence(r)
            for r in db.scalars(
                select(EnrollmentClaim)
                .where(EnrollmentClaim.application_id == app.id)
                .order_by(EnrollmentClaim.version.desc())
            )
        ],
        "findings": [
            evidence(r)
            for r in db.scalars(
                select(EnrollmentFinding)
                .where(EnrollmentFinding.application_id == app.id)
                .order_by(EnrollmentFinding.version.desc())
            )
        ],
        "verified_submission_first": verified_after(db, app) is not None,
        "pending_withdrawal": {
            "id": pending.id,
            "reason": pending.reason,
            "source_reference": pending.source_reference,
            "recorded_at": pending.recorded_at,
        }
        if pending and app.state in {"UNDER_REVIEW", "APPROVED"}
        else None,
        "storage": "OFFICIAL_ARCHIVE_REFERENCE_ONLY",
    }
