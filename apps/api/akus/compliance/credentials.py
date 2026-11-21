"""Serialized evidence commands. Provider authenticity and institutional credit are separate."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import service as apps
from akus.applications.models import Application, Reconciliation, Submission
from akus.applications.workflow_models import ReviewDecision
from akus.catalog import common
from akus.compliance.documents import inspect_pdf
from akus.compliance.models import (
    CredentialDocument,
    CredentialEvent,
    CredentialIdentity,
    CredentialMandate,
)
from akus.compliance.schemas import (
    Claim,
    Disposition,
    ExamProof,
    Registration,
    Verify,
)
from akus.exceptions.models import CaseEvent, HistoricalFinding
from akus.exceptions.service import exclusive
from akus.people.schemas import CommandResult


def grants(actor: Actor) -> Select[tuple[CredentialMandate]]:
    now = datetime.now(UTC)
    return select(CredentialMandate).where(
        CredentialMandate.reviewer_id == actor.person.id,
        CredentialMandate.valid_from <= now,
        CredentialMandate.valid_until > now,
        CredentialMandate.revoked_at.is_(None),
    )


def scope(actor: Actor) -> Select[tuple[Application]]:
    query = select(Application).where(Application.submitted_at.is_not(None))
    if "PRINCIPAL" in actor.roles:
        return query
    departments = [o.department_id for o in actor.offices if o.office in ("HOD", "ACTING_HOD")]
    return query.where(
        or_(
            Application.person_id == actor.person.id,
            Application.department_id.in_(departments),
            exists(grants(actor).where(CredentialMandate.application_id == Application.id)),
        )
    )


def latest(db: Session, aid: UUID) -> CredentialEvent | None:
    return db.scalar(
        select(CredentialEvent)
        .where(CredentialEvent.application_id == aid)
        .order_by(CredentialEvent.version.desc())
        .limit(1)
    )


def certified(db: Session, aid: UUID) -> CredentialEvent | HistoricalFinding | None:
    """An applicant assertion or rejected correction cannot revoke an independent finding."""
    active = db.scalar(
        select(CredentialEvent)
        .where(
            CredentialEvent.application_id == aid, CredentialEvent.kind.in_(["VERIFIED", "REVOKED"])
        )
        .order_by(CredentialEvent.version.desc())
        .limit(1)
    )
    archived = db.scalar(select(HistoricalFinding).where(HistoricalFinding.application_id == aid))
    if archived and (not active or archived.recorded_at > active.recorded_at):
        return archived
    return active


def require_single_subject(db: Session, aid: UUID, subject: UUID) -> None:
    """Q51 applies across both the active dossier and subsequent separation decisions."""
    other = str(subject)
    active = select(CredentialEvent.id).where(
        CredentialEvent.application_id == aid,
        CredentialEvent.kind == "VERIFIED",
        CredentialEvent.facts["subject_id"].as_string() != other,
    )
    archived = select(HistoricalFinding.id).where(
        HistoricalFinding.application_id == aid,
        HistoricalFinding.facts["subject_id"].as_string() != other,
    )
    relevance = (
        select(CaseEvent.id)
        .join(Reconciliation)
        .where(
            Reconciliation.application_id == aid,
            CaseEvent.action == "SUBJECT_RELEVANCE_VERIFIED",
            CaseEvent.facts["subject_id"].as_string() != other,
        )
    )
    if db.scalar(active.union_all(archived, relevance).limit(1)):
        raise HTTPException(423, "MULTIPLE_SUBJECT_USE_POLICY_PENDING_Q51")


def grant(
    db: Session, actor: Actor, app: Application, subject: UUID | None = None
) -> CredentialMandate | None:
    if app.person_id == actor.person.id or db.scalar(
        select(ReviewDecision.id)
        .where(ReviewDecision.application_id == app.id, ReviewDecision.actor_id == actor.person.id)
        .limit(1)
    ):
        return None
    query = grants(actor).where(CredentialMandate.application_id == app.id)
    if subject:
        query = query.where(CredentialMandate.subject_id == subject)
    return db.scalar(
        query.order_by(CredentialMandate.valid_from.desc(), CredentialMandate.id)
        .with_for_update(read=True)
        .limit(1)
    )


def write(
    db: Session,
    actor: Actor,
    key: UUID,
    aid: UUID,
    body: Registration | Verify | ExamProof | Disposition,
) -> CommandResult:
    # Hash and scan before acquiring the authority / admission gate.
    pdf = (
        inspect_pdf(body.attachment, body.document_digest)
        if isinstance(body, Registration) and body.attachment
        else None
    )
    exclusive(db)
    actor = common.refresh(db, actor, key)
    app, _ = apps.lock_application(db, aid)
    designation = None
    if isinstance(body, Registration):
        common.require_applicant(actor)
        if app.person_id != actor.person.id or app.episode_id != actor.episode.id:
            raise HTTPException(403, "OWN_CURRENT_EPISODE_REQUIRED")
        if app.state not in ("APPROVED", "OUTCOME_RECORDED", "UNDER_REVIEW"):
            raise HTTPException(409, "ACTIVE_SUBMITTED_APPLICATION_REQUIRED")
        kind = "ASSERTED"
        receipt: Claim | Verify | ExamProof | Disposition = Claim.model_validate(
            body.model_dump(exclude={"attachment"})
        )
    else:
        designation = grant(db, actor, app, body.subject_id if isinstance(body, Verify) else None)
        if not designation:
            raise HTTPException(403, "CERTIFICATE_OR_RELEVANCE_AUTHORITY_POLICY_PENDING")
        receipt = body
        kind = (
            "VERIFIED"
            if isinstance(body, Verify)
            else "EXAM_VERIFIED"
            if isinstance(body, ExamProof)
            else body.outcome
        )
    op = f"CREDENTIAL_{kind}:{aid}"
    if result := common.replay(db, actor, key, op, receipt):
        if isinstance(body, Registration) and bool(
            db.get_one(CredentialEvent, result.id).document_id
        ) != (body.attachment is not None):
            raise HTTPException(409, "IDEMPOTENCY_KEY_REUSED")
        return result
    if not isinstance(body, Registration):
        common.require_person_evidence(db, body.source_reference, body.document_digest)
    previous = latest(db, aid)
    if body.expected_version != (previous.version if previous else 0):
        raise HTTPException(409, "CREDENTIAL_VERSION_CONFLICT")
    if not db.get(Submission, aid):
        raise HTTPException(409, "SUBMITTED_APPLICATION_REQUIRED")
    archived = db.scalar(select(HistoricalFinding).where(HistoricalFinding.application_id == aid))
    original = (
        previous
        if previous and (not archived or previous.recorded_at > archived.recorded_at)
        else archived
    )
    facts = receipt.model_dump(mode="json")
    document = None
    if pdf:
        facts["document_scan"] = pdf.status
        facts["scanner_version"] = pdf.scanner_version
        document = db.scalar(
            select(CredentialDocument).where(CredentialDocument.digest == body.document_digest)
        )
        if document and document.application_id != aid:
            raise HTTPException(409, "DOCUMENT_IDENTITY_CONFLICT")
        if not document:
            document = CredentialDocument(
                id=uuid4(),
                application_id=aid,
                digest=body.document_digest,
                content=pdf.content,
                scan=pdf.status,
            )
            db.add(document)
            db.flush()
    if not isinstance(body, Registration):
        if not original:
            raise HTTPException(409, "ORIGINAL_EVIDENCE_REQUIRED")
        if body.observed_at < datetime.fromisoformat(original.facts["observed_at"]):
            raise HTTPException(409, "STALE_VERIFICATION_SOURCE")
        facts["previous_event_id"] = str(original.id)
        assert designation
        facts["authority_basis"] = designation.basis
        facts["proof_class"] = "INDEPENDENT_OFFICIAL_RECORD"
    else:
        facts["proof_class"] = "PERSON_ASSERTION"
    if isinstance(body, Disposition) and body.outcome == "REVOKED":
        old = certified(db, aid)
        if old:
            facts = {
                k: old.facts.get(k)
                for k in (
                    "certificate_key",
                    "actual_exam_on",
                    "actual_exam_at",
                    "issued_on",
                    "score_percent",
                    "subject_id",
                    "sitting",
                )
            } | facts
    if isinstance(body, Disposition):
        if body.outcome == "REJECTED" and (not previous or previous.kind != "ASSERTED"):
            raise HTTPException(409, "PENDING_ASSERTION_REQUIRED")
        if (
            body.outcome == "REVOKED"
            and not archived
            and not db.scalar(
                select(CredentialIdentity.certificate_key)
                .where(CredentialIdentity.application_id == aid)
                .limit(1)
            )
        ):
            raise HTTPException(409, "VERIFIED_CREDENTIAL_REQUIRED")
        if (
            body.outcome == "REVOKED"
            and isinstance(official := certified(db, aid), CredentialEvent)
            and official.kind == "REVOKED"
        ):
            raise HTTPException(409, "DISPOSITION_ALREADY_RECORDED")
        if previous and previous.kind == body.outcome:
            raise HTTPException(409, "DISPOSITION_ALREADY_RECORDED")
    if isinstance(body, Verify):
        binding = db.get(CredentialIdentity, body.certificate_key)
        if (binding and binding.application_id != aid) or db.scalar(
            select(HistoricalFinding.id)
            .where(
                HistoricalFinding.certificate_key == body.certificate_key,
                HistoricalFinding.application_id != aid,
            )
            .limit(1)
        ):
            raise HTTPException(409, "CERTIFICATE_IDENTITY_CONFLICT")
        if body.subject_id:
            from akus.sources.models import TeachingAssignment

            require_single_subject(db, aid, body.subject_id)
            if not db.scalar(
                select(TeachingAssignment.id)
                .where(
                    TeachingAssignment.episode_id == app.episode_id,
                    TeachingAssignment.subject_id == body.subject_id,
                    TeachingAssignment.voided.is_(False),
                )
                .limit(1)
            ):
                raise HTTPException(409, "SUBJECT_OUTSIDE_EMPLOYMENT_EPISODE")
        if not binding:
            db.add(CredentialIdentity(certificate_key=body.certificate_key, application_id=aid))
    event = CredentialEvent(
        id=uuid4(),
        application_id=aid,
        actor_id=actor.person.id,
        version=body.expected_version + 1,
        kind=kind,
        mandate_id=designation.id if designation else None,
        document_id=document.id if document else None,
        facts=facts,
        recorded_at=datetime.now(UTC),
    )
    if isinstance(body, Verify):
        from sqlalchemy import func

        from akus.compliance.assessment import academic_start, eligibility
        from akus.exceptions.history import archived_obligation, silver_status
        from akus.models import AcademicYear
        from akus.sources.models import TeachingAssignment

        subject_id = body.subject_id
        previous_certificate = certified(db, aid)
        if (
            subject_id is None
            and previous_certificate
            and previous_certificate.facts.get("certificate_key") == body.certificate_key
            and (
                isinstance(previous_certificate, HistoricalFinding)
                or previous_certificate.kind == "VERIFIED"
            )
        ):
            # A numerical correction preserves an independently established mapping for
            # this credential. Keep the original decision identity and its rationale.
            relevance = db.scalar(
                select(CaseEvent)
                .join(Reconciliation)
                .where(
                    Reconciliation.application_id == aid,
                    CaseEvent.action == "SUBJECT_RELEVANCE_VERIFIED",
                    CaseEvent.facts["finding_id"].as_string() == str(previous_certificate.id),
                )
                .order_by(CaseEvent.version.desc())
                .limit(1)
            )
            source = relevance or previous_certificate
            if source.facts.get("subject_id"):
                subject_id = UUID(source.facts["subject_id"])
                facts = facts | {
                    "subject_id": str(subject_id),
                    "relevance_basis": source.facts["relevance_basis"],
                    "relevance_finding_id": source.facts.get(
                        "relevance_finding_id", str(source.id)
                    ),
                }
        submission = db.get_one(Submission, aid)
        basis = eligibility(db, app, event, submission)
        year = db.scalar(
            select(AcademicYear.label).where(
                AcademicYear.starts_on == academic_start(body.actual_exam_on)
            )
        )
        first = (
            db.scalar(
                select(func.min(TeachingAssignment.starts_on)).where(
                    TeachingAssignment.episode_id == app.episode_id,
                    TeachingAssignment.subject_id == subject_id,
                    TeachingAssignment.voided.is_(False),
                    TeachingAssignment.starts_on <= apps.today(),
                )
            )
            if subject_id
            else None
        )
        deadline = None
        if first:
            try:
                deadline = first.replace(year=first.year + 2).isoformat()
            except ValueError:
                pass
        ruling = (
            archived_obligation(db, app.episode_id, subject_id, first, apps.today())
            if subject_id and first
            else None
        )
        silver = (
            silver_status(basis, body.score_percent, deadline, body.actual_exam_on)
            if subject_id
            else "RELEVANCE_UNASSESSED"
        )
        if silver == "VERIFIED_ON_TIME" and not ruling:
            silver = "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
        event.facts = facts | {
            "eligibility": basis,
            "academic_year": year
            or f"{academic_start(body.actual_exam_on).year}–{str(academic_start(body.actual_exam_on).year + 1)[2:]}",
            "course_id": str(app.course_id),
            "duration_weeks": submission.facts["metadata"]["duration_weeks"],
            "subject_deadline": deadline,
            "silver": silver,
            "archived_obligation_id": str(ruling.id) if ruling else None,
        }
    db.add(event)
    db.flush()
    if isinstance(body, Verify):
        for later in db.scalars(
            select(Application).where(
                Application.person_id == app.person_id,
                Application.course_id == app.course_id,
                Application.submitted_at > app.submitted_at,
                Application.state.in_(["APPROVED", "OUTCOME_RECORDED"]),
            )
        ):
            # A later source revision for the same credential doesn't reopen an adjudicated case.
            if not db.scalar(
                select(CredentialEvent.id)
                .where(
                    CredentialEvent.application_id == aid,
                    CredentialEvent.kind == "VERIFIED",
                    CredentialEvent.version < event.version,
                )
                .limit(1)
            ):
                apps.case(
                    db,
                    later,
                    "INTEGRITY",
                    "PRIOR_CERTIFICATE_AUTHORITY_POLICY_PENDING",
                    {
                        "credential_application_id": str(aid),
                        "credential_event_id": str(event.id),
                        "recognition": "SUSPENDED",
                    },
                )
    from akus.compliance.assessment import capture
    from akus.people.models import EmploymentEpisode

    episode = db.get(EmploymentEpisode, app.episode_id)
    assert episode
    capture(db, episode)
    audit = {
        "event_id": str(event.id),
        "application_id": str(aid),
        "version": event.version,
        "digest": body.document_digest,
        "mandate_id": str(designation.id) if designation else None,
    }
    apps.notice(db, app, "CREDENTIAL_" + kind, audit)
    return common.finish(db, actor, key, op, receipt, event.id, audit, app.department_id)


def timeline(db: Session, app: Application, actor: Actor) -> dict[str, Any]:
    rows = list(
        db.scalars(
            select(CredentialEvent)
            .where(CredentialEvent.application_id == app.id)
            .order_by(CredentialEvent.version.desc())
        )
    )
    from akus.sources.models import Subject, TeachingAssignment

    archived = db.scalar(
        select(HistoricalFinding).where(HistoricalFinding.application_id == app.id)
    )
    g = grant(db, actor, app)
    subjects = db.execute(
        select(Subject.id, Subject.name)
        .join(TeachingAssignment)
        .where(
            TeachingAssignment.episode_id == app.episode_id, TeachingAssignment.voided.is_(False)
        )
        .distinct()
        .order_by(Subject.name)
    ).all()
    authorized_subjects = (
        set(
            db.scalars(
                grants(actor)
                .where(CredentialMandate.application_id == app.id)
                .with_only_columns(CredentialMandate.subject_id)
            )
        )
        if g
        else set()
    )
    # Older assertions only recorded the initial immutable scan on the document.
    document_scans = {
        r.id: r.facts.get("document_scan") or db.get_one(CredentialDocument, r.document_id).scan
        for r in rows
        if r.document_id
    }
    return {
        "subjects": [
            {"id": sid, "name": name, "can_verify": sid in authorized_subjects}
            for sid, name in subjects
        ],
        "archive": {"id": archived.id, "recorded_at": archived.recorded_at, "facts": archived.facts}
        if archived
        else None,
        "application_id": app.id,
        "version": rows[0].version if rows else 0,
        "status": rows[0].kind
        if rows and (not archived or rows[0].recorded_at > archived.recorded_at)
        else "VERIFIED"
        if archived
        else "AWAITING_EVIDENCE",
        "can_register": actor.view().applicant_eligible
        and app.person_id == actor.person.id
        and app.episode_id == actor.episode.id
        and app.state in ("APPROVED", "OUTCOME_RECORDED", "UNDER_REVIEW"),
        "can_verify": bool(g),
        "authority": g.basis if g else "FORMAL_DESIGNATION_REQUIRED",
        "events": [
            {
                "id": r.id,
                "kind": r.kind,
                "version": r.version,
                "recorded_at": r.recorded_at,
                "actor_id": r.actor_id,
                "document_id": r.document_id,
                "document_state": document_scans.get(r.id),
                "can_download": bool(
                    r.document_id
                    and (actor.person.id == app.person_id or g)
                    and document_scans.get(r.id) == "CLEAN"
                ),
                "facts": r.facts,
            }
            for r in rows
        ],
    }
