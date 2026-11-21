"""Effective-date separation and independent integrity decisions.

Source changes and multi-application closures take the existing exclusive authority
gate first. All quota effects then follow the normal offering/application/pool order.
"""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications import participation
from akus.applications import service as apps
from akus.applications.models import Allocation, Application, Reconciliation
from akus.catalog import common
from akus.catalog.models import AcademicEvent, Offering
from akus.catalog.service import snapshot
from akus.config import Settings
from akus.exceptions.models import CaseEvent, Departure, IntegrityMandate, SeparationSnapshot
from akus.exceptions.schemas import IST, Closure, Order, RosterProof
from akus.models import AuditEvent
from akus.people.models import EmploymentEpisode
from akus.people.schemas import CommandResult
from akus.sources.models import SourceRevision, TeachingAssignment


def exclusive(db: Session) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(8210402)"))


def last(db: Session, cid: UUID) -> CaseEvent | None:
    return db.scalar(
        select(CaseEvent)
        .where(CaseEvent.case_id == cid)
        .order_by(CaseEvent.version.desc())
        .limit(1)
    )


def append(
    db: Session,
    c: Reconciliation,
    action: str,
    facts: dict[str, Any],
    actor: Actor | None = None,
    office: UUID | None = None,
) -> CaseEvent:
    old = last(db, c.id)
    e = CaseEvent(
        id=uuid4(),
        case_id=c.id,
        version=old.version + 1 if old else 1,
        action=action,
        recorded_at=datetime.now(UTC),
        facts=facts,
        actor_id=actor.person.id if actor else None,
        office_id=office,
    )
    db.add(e)
    db.flush()
    return e


def active_order(db: Session, app: Application) -> Departure | None:
    return db.scalar(
        select(Departure).where(
            Departure.episode_id == app.episode_id,
            Departure.effective_on <= apps.today(),
            or_(Departure.effective_at.is_(None), Departure.effective_at <= datetime.now(UTC)),
        )
    )


def freeze(db: Session, order: Departure) -> None:
    if db.get(SeparationSnapshot, order.id):
        return
    from datetime import time

    from akus.compliance.models import CredentialEvent
    from akus.exceptions.history import archived_obligation, comparison, episode_report

    cutoff = order.effective_at or datetime.combine(order.effective_on, time.min, IST)
    timely: dict[str, str] = {}
    for aid in db.scalars(
        select(CredentialEvent.application_id)
        .join(Application)
        .where(
            Application.episode_id == order.episode_id,
            CredentialEvent.kind == "VERIFIED",
            CredentialEvent.recorded_at <= cutoff,
        )
        .distinct()
    ):
        finding = episode_report(db, order.episode_id, aid, cutoff)["finding"]
        if (
            finding
            and finding["silver"] == "VERIFIED_ON_TIME"
            and comparison(
                date.fromisoformat(finding["actual_exam_on"]),
                datetime.fromisoformat(finding["actual_exam_at"])
                if finding.get("actual_exam_at")
                else None,
                order.effective_on,
                order.effective_at,
            )
            == -1
        ):
            timely[finding["subject_id"]] = str(finding["id"])

    subjects = []
    # A backdated order may arrive after HR corrected a teaching allocation.
    # Replay the revision known at the effective boundary so a later change
    # cannot rewrite the original deadline. Date-only orders use the last
    # unambiguously known facts at the start of that institutional day.
    revisions = db.scalars(
        select(SourceRevision)
        .join(TeachingAssignment, TeachingAssignment.id == SourceRevision.entity_id)
        .where(
            SourceRevision.entity_type == TeachingAssignment.__tablename__,
            TeachingAssignment.episode_id == order.episode_id,
            SourceRevision.recorded_at <= cutoff,
        )
        .distinct(SourceRevision.entity_id)
        .order_by(
            SourceRevision.entity_id, SourceRevision.recorded_at.desc(), SourceRevision.id.desc()
        )
    )
    earliest: dict[UUID, tuple[date, SourceRevision]] = {}
    for revision in revisions:
        facts = revision.after
        first = date.fromisoformat(facts["starts_on"])
        subject = UUID(facts["subject_id"])
        if facts["voided"] or first > order.effective_on:
            continue
        if subject not in earliest or first < earliest[subject][0]:
            earliest[subject] = (first, revision)
    for subject, (first, revision) in earliest.items():
        try:
            deadline = first.replace(year=first.year + 2)
        except ValueError:
            deadline = None
        accepted = archived_obligation(db, order.episode_id, subject, first, order.effective_on)
        if accepted and accepted.recorded_at > cutoff:
            accepted = None
        subjects.append(
            {
                "subject_id": str(subject),
                "archived_obligation_id": str(accepted.id) if accepted else None,
                "first_assignment": first.isoformat(),
                "deadline": deadline.isoformat() if deadline else None,
                "teaching_revision_id": str(revision.id),
                "knowledge_cutoff": cutoff.isoformat(),
                "achievement_at_separation": timely.get(str(subject)),
                "status_at_separation": "VERIFIED_ON_TIME"
                if accepted and str(subject) in timely
                else "DEADLINE_POLICY_PENDING"
                if not deadline
                else "DEADLINE_PASSED_ACCEPTANCE_PENDING_IO02"
                if not accepted and deadline < order.effective_on
                else "OVERDUE_PENDING_EVIDENCE"
                if deadline < order.effective_on
                else "UNRESOLVED_AT_SEPARATION",
            }
        )
    db.add(
        SeparationSnapshot(departure_id=order.id, subjects=subjects, recorded_at=datetime.now(UTC))
    )
    db.flush()


def record_order(
    db: Session, actor: Actor, key: UUID, episode_id: UUID, body: Order, cfg: Settings
) -> CommandResult:
    exclusive(db)
    actor = common.refresh(db, actor, key)
    if "ADMIN" not in actor.roles:
        raise HTTPException(403, "HR_SOURCE_AUTHORITY_REQUIRED")
    op = f"PERMANENT_DEPARTURE:{episode_id}"
    if r := common.replay(db, actor, key, op, body):
        return r
    episode = db.get(EmploymentEpisode, episode_id)
    if not episode or not episode.is_faculty or episode.ends_before != body.effective_on:
        raise HTTPException(409, "MATCHING_OFFICIAL_EPISODE_END_REQUIRED")
    if db.scalar(select(Departure.id).where(Departure.episode_id == episode_id)):
        raise HTTPException(409, "PERMANENT_ORDER_ALREADY_RECORDED")
    order = Departure(
        id=uuid4(),
        episode_id=episode_id,
        effective_at=body.effective_at,
        effective_on=body.effective_on,
        recorded_at=datetime.now(UTC),
        actor_id=actor.person.id,
        proof=body.model_dump(mode="json"),
    )
    db.add(order)
    db.flush()
    process_order(db, order, cfg)
    return common.finish(
        db, actor, key, op, body, order.id, order.proof | {"episode_id": str(episode_id)}
    )


def enrolled_order(db: Session, app: Application, order: Departure) -> tuple[str, str | None]:
    finding = participation.verified_after(db, app)
    if not finding:
        return "UNVERIFIED", None
    if order.effective_at and finding.enrolled_at:
        enrolled, departed = finding.enrolled_at, order.effective_at
        comparison = (
            "BEFORE" if enrolled < departed else "AFTER" if enrolled > departed else "UNCERTAIN"
        )
    else:
        day = finding.enrolled_on or (
            finding.enrolled_at.astimezone(IST).date() if finding.enrolled_at else None
        )
        comparison = (
            "BEFORE"
            if day and day < order.effective_on
            else "AFTER"
            if day and day > order.effective_on
            else "UNCERTAIN"
        )
    return comparison, str(finding.id)


def classify(
    db: Session, app: Application, offering: Offering, order: Departure, cfg: Settings
) -> tuple[str, dict[str, Any]]:
    facts: dict[str, Any] = {
        "departure_id": str(order.id),
        "episode_id": str(order.episode_id),
        "effective_on": order.effective_on.isoformat(),
        "effective_at": order.effective_at.isoformat() if order.effective_at else None,
        "source_reference": order.proof["source_reference"],
        "document_digest": order.proof["document_digest"],
        "order_recorded_at": order.recorded_at.isoformat(),
    }
    if db.scalar(
        select(Reconciliation.id).where(
            Reconciliation.application_id == app.id,
            Reconciliation.kind == "INTEGRITY",
            Reconciliation.status == "OPEN",
        )
    ):
        return "CONCURRENT_INTEGRITY_POLICY_PENDING", facts
    if (
        not app.submitted_at
        or order.effective_on < app.submitted_at.astimezone(IST).date()
        or (order.effective_at and order.effective_at < app.submitted_at)
    ):
        return "SUBMISSION_AFTER_SEPARATION_RECONCILIATION", facts
    try:
        source = apps.verified_commencement(db, offering, cfg)
    except HTTPException:
        return "COMMENCEMENT_VERIFICATION_REQUIRED", facts
    start = date.fromisoformat(source.metadata_json["starts_on"])
    before, finding = enrolled_order(db, app, order)
    facts.update(
        starts_on=start.isoformat(),
        commencement_snapshot_id=str(source.id),
        enrollment_finding_id=finding,
        enrollment_relative_to_separation=before,
    )
    if start < order.effective_on:
        return "Q45", facts
    if start == order.effective_on:
        return "Q47_CHRONOLOGY_REVIEW", facts
    if before == "AFTER":
        return "Q43", facts
    if before == "BEFORE":
        return "Q44_HOD_REVIEW", facts
    return "ENROLLMENT_CHRONOLOGY_REQUIRED", facts


def close(
    db: Session,
    app: Application,
    c: Reconciliation,
    reason: str,
    facts: dict[str, Any],
    actor: Actor | None = None,
    office: UUID | None = None,
) -> None:
    allocation = db.get(Allocation, app.id)
    if not allocation or allocation.state == "RELEASED":
        raise HTTPException(409, "COUNTED_SEAT_REQUIRED")
    facts = facts | {
        "pool_id": str(allocation.pool_id),
        "previous_state": app.state,
        "previous_allocation_state": allocation.state,
    }
    decision = append(db, c, reason, facts, actor, office)
    if reason == "INVALIDATE":
        # Chronology is still unadjudicated. Its seat-closure task has no
        # remaining action once the independent integrity decision takes effect.
        pending = db.scalar(
            select(Reconciliation)
            .where(
                Reconciliation.application_id == app.id,
                Reconciliation.kind == "SEPARATION",
                Reconciliation.status == "OPEN",
            )
            .with_for_update()
        )
        if pending:
            superseded = "CLOSED_BY_INTEGRITY_INVALIDATION"
            append(
                db,
                pending,
                superseded,
                {
                    "integrity_decision_id": str(decision.id),
                    "integrity_case_id": str(c.id),
                    "pool_id": facts["pool_id"],
                    "chronology": "UNADJUDICATED",
                },
                actor,
            )
            apps.resolve_case(db, app, "SEPARATION", superseded)
    apps.resolve_case(db, app, c.kind, reason)
    apps.release(db, app, actor, reason + "_RELEASE")
    app.state = "INVALIDATED" if reason == "INVALIDATE" else "SEPARATED"
    app.next_office = None
    app.version += 1
    db.add(
        AcademicEvent(
            entity_id=app.id,
            kind=reason + "_RELEASE",
            actor_id=actor.person.id if actor else None,
            department_id=app.department_id,
            data=facts,
        )
    )
    db.add(
        AuditEvent(
            action=reason + "_RELEASE",
            details={
                "application_id": str(app.id),
                "case_id": str(c.id),
                "pool_id": facts["pool_id"],
            },
        )
    )


def process_order(db: Session, order: Departure, cfg: Settings) -> None:
    if order.effective_on > apps.today() or (
        order.effective_at and order.effective_at > datetime.now(UTC)
    ):
        return
    episode = db.get(EmploymentEpisode, order.episode_id)
    assert episode
    matching = episode.ends_before == order.effective_on
    first_freeze = matching and db.get(SeparationSnapshot, order.id) is None
    if first_freeze:
        freeze(db, order)
    for aid in db.scalars(
        select(Application.id)
        .where(
            Application.episode_id == order.episode_id,
            Application.state.in_(["UNDER_REVIEW", "APPROVED", "SEPARATED"]),
        )
        .order_by(Application.offering_id, Application.id)
    ).all():
        app, offering = apps.lock_application(db, aid)
        if app.state == "SEPARATED":
            closure = db.scalar(
                select(CaseEvent)
                .join(Reconciliation)
                .where(
                    Reconciliation.application_id == app.id,
                    Reconciliation.kind == "SEPARATION",
                    CaseEvent.action.in_(["Q43", "Q44", "Q45", "Q47"]),
                )
            )
            accepted = snapshot(db, offering)
            revised_start = accepted.metadata_json.get("starts_on") if accepted else None
            if not matching or (closure and revised_start != closure.facts.get("starts_on")):
                apps.case(
                    db,
                    app,
                    "SOURCE_CORRECTION",
                    "RELEASED_SEAT_CORRECTION_POLICY_PENDING",
                    {
                        "departure_id": str(order.id),
                        "reviewed_start": closure.facts.get("starts_on") if closure else None,
                        "current_start": revised_start,
                        "current_episode_end": str(episode.ends_before),
                    },
                )
            continue
        reason, facts = (
            classify(db, app, offering, order, cfg)
            if matching
            else ("HR_SOURCE_CORRECTION_REQUIRED", {"departure_id": str(order.id)})
        )
        apps.case(db, app, "SEPARATION", reason, facts)
        db.flush()
        c = db.scalar(
            select(Reconciliation).where(
                Reconciliation.application_id == aid, Reconciliation.kind == "SEPARATION"
            )
        )
        assert c
        if reason in {"Q43", "Q45"}:
            close(db, app, c, reason, facts)
    if first_freeze:
        from akus.compliance.assessment import capture

        capture(db, episode)


def mandate(
    db: Session, actor: Actor, c: Reconciliation, app: Application
) -> IntegrityMandate | None:
    if actor.person.id == app.person_id:
        return None
    # Prior adjudicators, evidence verifiers and the applicant cannot decide integrity.
    entities = [app.id]
    for e in db.scalars(select(CaseEvent).where(CaseEvent.case_id == c.id)):
        for source_id in ("attempt_id", "historical_finding_id", "credential_event_id"):
            if e.facts.get(source_id):
                entities.append(UUID(e.facts[source_id]))
    if db.scalar(
        select(AcademicEvent.id)
        .where(
            AcademicEvent.entity_id.in_(entities),
            AcademicEvent.actor_id == actor.person.id,
            AcademicEvent.kind.in_(
                [
                    "APPLICATION_REVIEW",
                    "PRIOR_OUTCOME_DECIDED",
                    "ENROLLMENT_VERIFIED",
                    "HISTORICAL_CERTIFICATE",
                    "CREDENTIAL_VERIFIED",
                ]
            ),
        )
        .limit(1)
    ):
        return None
    now = datetime.now(UTC)
    return db.scalar(
        select(IntegrityMandate)
        .where(
            IntegrityMandate.case_id == c.id,
            IntegrityMandate.reviewer_id == actor.person.id,
            IntegrityMandate.valid_from <= now,
            IntegrityMandate.valid_until > now,
            IntegrityMandate.revoked_at.is_(None),
        )
        .with_for_update(read=True)
    )


def reviewed_enrollment_order(
    db: Session, app: Application, order: Departure, body: Closure
) -> int | None:
    from akus.exceptions.history import comparison

    instant = body.enrollment_at
    day = instant.astimezone(IST).date() if instant else body.enrollment_on
    prior = participation.finding_current(db, app.id)
    if prior and prior.outcome == "VERIFIED":
        prior_day = (
            prior.enrolled_at.astimezone(IST).date() if prior.enrolled_at else prior.enrolled_on
        )
        if day and (
            day != prior_day or (instant and prior.enrolled_at and instant != prior.enrolled_at)
        ):
            raise HTTPException(409, "CONFLICTING_ENROLLMENT_EVIDENCE")
        if participation.verified_after(db, app):
            day, instant = day or prior_day, instant or prior.enrolled_at
    if (
        not day
        or not app.submitted_at
        or comparison(day, instant, app.submitted_at.astimezone(IST).date(), app.submitted_at) != 1
    ):
        return None
    return comparison(day, instant, order.effective_on, order.effective_at or body.separation_at)


def decide(
    db: Session, actor: Actor, key: UUID, cid: UUID, kind: str, body: Closure, cfg: Settings
) -> CommandResult:
    exclusive(db)
    actor = common.refresh(db, actor, key)
    c = db.get(Reconciliation, cid)
    if not c or c.kind != kind:
        raise HTTPException(404, "CASE_NOT_FOUND")
    app, offering = apps.lock_application(db, c.application_id)
    if app.person_id == actor.person.id:
        raise HTTPException(403, "SELF_REVIEW_PROHIBITED")
    office = None
    facts = body.model_dump(mode="json")
    if kind == "INTEGRITY":
        grant = mandate(db, actor, c, app)
        if not grant:
            raise HTTPException(403, "INTEGRITY_AUTHORITY_POLICY_PENDING")
        facts.update(mandate_id=str(grant.id), appointment_basis=grant.basis)
    else:
        office = common.require_hod(actor, app.department_id).id
    op = f"{kind}_DISPOSITION:{cid}"
    if r := common.replay(db, actor, key, op, body):
        return r
    previous = last(db, c.id)
    if not previous or previous.id != body.expected_event_id or c.status != "OPEN":
        raise HTTPException(409, "CASE_CHANGED_REFRESH_REQUIRED")
    if kind == "INTEGRITY":
        if body.finding not in {"UPHOLD", "INVALIDATE"}:
            raise HTTPException(422, "INTEGRITY_FINDING_REQUIRED")
        if body.finding == "INVALIDATE":
            close(db, app, c, "INVALIDATE", facts | {"recognition": "INELIGIBLE"}, actor)
        else:
            append(
                db,
                c,
                "UPHOLD",
                facts
                | {
                    "recognition": "ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT",
                    "application_id": str(app.id),
                },
                actor,
            )
            apps.resolve_case(db, app, "INTEGRITY", "UPHELD_FOR_THIS_APPLICATION")
    else:
        order = active_order(db, app)
        episode = db.get(EmploymentEpisode, app.episode_id)
        if not order or not episode or episode.ends_before != order.effective_on:
            raise HTTPException(409, "CURRENT_PERMANENT_ORDER_REQUIRED")
        reason, current = classify(db, app, offering, order, cfg)
        if current != c.context or reason != c.reason:
            raise HTTPException(409, "SEPARATION_FACTS_CHANGED")
        if reason != "Q47_CHRONOLOGY_REVIEW" and (body.separation_at or body.commencement_at):
            raise HTTPException(422, "ADDITIONAL_TIMESTAMPS_REQUIRE_SAME_DAY_REVIEW")
        relation = reviewed_enrollment_order(db, app, order, body)
        facts = current | facts
        if body.finding == "Q44" and reason in {"Q44_HOD_REVIEW", "ENROLLMENT_CHRONOLOGY_REQUIRED"}:
            if relation != -1:
                raise HTTPException(423, "VERIFIED_ENROLLMENT_ORDER_REQUIRED")
            final = "Q44"
        elif reason == "Q47_CHRONOLOGY_REVIEW":
            if body.finding == "INDETERMINATE":
                if body.commencement_at or body.separation_at:
                    raise HTTPException(422, "EXPLAIN_OBSERVED_ORDER")
                final = "Q47"
            else:
                sep = order.effective_at or body.separation_at
                start = body.commencement_at
                if (
                    not sep
                    or not start
                    or sep.astimezone(IST).date() != order.effective_on
                    or start.astimezone(IST).date() != order.effective_on
                    or (
                        order.effective_at
                        and body.separation_at
                        and order.effective_at != body.separation_at
                    )
                ):
                    raise HTTPException(423, "MATCHING_OFFICIAL_TIMESTAMPS_REQUIRED")
                if body.finding == "AFTER_START" and sep > start:
                    final = "Q45"
                elif body.finding == "BEFORE_START" and sep < start and relation in {-1, 1}:
                    final = "Q44" if relation == -1 else "Q43"
                else:
                    raise HTTPException(423, "VERIFIED_CHRONOLOGY_REQUIRED")
        else:
            raise HTTPException(423, "SEPARATION_EVIDENCE_OR_AUTHORITY_PENDING")
        close(db, app, c, final, facts, actor, office)
    from akus.compliance.assessment import capture

    capture(db, db.get_one(EmploymentEpisode, app.episode_id))
    return common.finish(db, actor, key, op, body, c.id, facts, app.department_id)


def scan_due(db: Session, cfg: Settings) -> None:
    # Take the exclusive gate only when there are permanent orders to reconcile.
    if not db.scalar(select(Departure.id).where(Departure.effective_on <= apps.today()).limit(1)):
        return
    exclusive(db)
    for order in db.scalars(
        select(Departure).where(Departure.effective_on <= apps.today()).order_by(Departure.id)
    ):
        process_order(db, order, cfg)


def verify_absence(
    db: Session, actor: Actor, key: UUID, cid: UUID, body: RosterProof, cfg: Settings
) -> CommandResult:
    """Authenticate an exact, complete negative roster under its own appointment."""
    from akus.exceptions.history import authorized

    exclusive(db)
    actor = common.refresh(db, actor, key)
    c = db.get(Reconciliation, cid)
    if not c or c.kind != "SEPARATION":
        raise HTTPException(404, "CASE_NOT_FOUND")
    app, offering = apps.lock_application(db, c.application_id)
    grant = authorized(db, actor, c, app, "ENROLLMENT_ABSENCE")
    if not grant:
        raise HTTPException(403, "ENROLLMENT_ABSENCE_AUTHORITY_POLICY_PENDING")
    op = f"ENROLLMENT_ABSENCE:{cid}"
    if replay := common.replay(db, actor, key, op, body):
        return replay
    common.require_person_evidence(db, body.source_reference, body.document_digest)
    previous = last(db, cid)
    if not previous or previous.id != body.expected_event_id or c.status != "OPEN":
        raise HTTPException(409, "CASE_CHANGED_REFRESH_REQUIRED")
    order = active_order(db, app)
    episode = db.get(EmploymentEpisode, app.episode_id)
    if not order or not episode or episode.ends_before != order.effective_on:
        raise HTTPException(423, "MATCHING_OFFICIAL_EPISODE_END_REQUIRED")
    reason, facts = classify(db, app, offering, order, cfg)
    if reason != "ENROLLMENT_CHRONOLOGY_REQUIRED" or participation.known_enrollment(db, app):
        raise HTTPException(423, "ENROLLMENT_CONFLICT_OR_CHRONOLOGY_REVIEW")
    if (
        body.absence_through < order.effective_at
        if order.effective_at
        else body.absence_through.astimezone(IST).date() <= order.effective_on
    ):
        raise HTTPException(423, "ROSTER_MUST_COVER_SEPARATION")
    decision = (
        facts
        | body.model_dump(mode="json")
        | {
            "mandate_id": str(grant.id),
            "appointment_basis": grant.basis,
            "enrollment_relative_to_separation": "VERIFIED_ABSENT_THROUGH_DEPARTURE",
        }
    )
    append(db, c, "NON_ENROLLMENT_VERIFIED", decision, actor)
    close(db, app, c, "Q43", decision)
    from akus.compliance.assessment import capture

    capture(db, db.get_one(EmploymentEpisode, app.episode_id))
    return common.finish(db, actor, key, op, body, c.id, decision, app.department_id)
