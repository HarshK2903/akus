"""Atomic admission and lawful local closure; no provider participation is inferred."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.applications.models import (
    AcademicNotice,
    Allocation,
    Application,
    Ledger,
    Reconciliation,
    Submission,
)
from akus.applications.schemas import DraftWrite, Review, Submit, Withdraw
from akus.applications.workflow_models import DraftRevision, EnrollmentClaim, ReviewDecision
from akus.catalog import common
from akus.catalog.models import MappingAnchor, Offering, ProviderSnapshot
from akus.catalog.service import current_mapping, snapshot, source_usable, topic_candidates
from akus.config import Settings
from akus.models import AcademicYear, WorkJob
from akus.people.models import DepartmentAssignment, EmploymentEpisode, OfficeAppointment, Person
from akus.people.schemas import CommandResult
from akus.quotas.models import QuotaPool


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def notice(db: Session, app: Application, kind: str, facts: dict[str, Any]) -> None:
    db.add(AcademicNotice(application_id=app.id, kind=kind, facts=facts))


def case(
    db: Session,
    app: Application,
    kind: str,
    reason: str,
    data: dict[str, Any],
    source: UUID | None = None,
) -> None:
    record = db.scalar(
        select(Reconciliation)
        .where(Reconciliation.application_id == app.id, Reconciliation.kind == kind)
        .with_for_update()
    )
    # Application row is the lock for case creation and refresh; no check/insert race.
    if (
        record
        and record.status == "OPEN"
        and record.reason == reason
        and record.context == data
        and record.snapshot_id == source
    ):
        return
    if not record:
        record = Reconciliation(id=uuid4(), application_id=app.id, kind=kind)
        db.add(record)
    record.status, record.reason, record.context, record.snapshot_id = "OPEN", reason, data, source
    record.updated_at = datetime.now(UTC)
    notice(db, app, kind, {"reason": reason, **data})
    if kind in {"INTEGRITY", "SEPARATION"}:
        from akus.exceptions.service import append

        db.flush()
        append(db, record, "EVIDENCE_RECORDED", data | {"reason": reason})


def resolve_case(db: Session, app: Application, kind: str, reason: str) -> None:
    record = db.scalar(
        select(Reconciliation)
        .where(Reconciliation.application_id == app.id, Reconciliation.kind == kind)
        .with_for_update()
    )
    if record and record.status == "OPEN":
        record.status, record.reason, record.updated_at = "RESOLVED", reason, datetime.now(UTC)
        notice(db, app, kind + "_RESOLVED", {"reason": reason})


def can_read(actor: Actor, app: Application) -> None:
    if app.person_id == actor.person.id or set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        return
    if (
        app.state != "DRAFT"
        and app.department_id in actor.scopes
        and set(actor.roles) & {"HOD", "DRC_HEAD"}
    ):
        return
    raise HTTPException(403, "APPLICATION_ACCESS_DENIED")


def resolve_released_cases(db: Session, app: Application) -> None:
    # These cases concern a live counted allocation. Closing their work item after
    # release does not authenticate an assertion or settle an institutional policy.
    kinds = list(
        db.scalars(
            select(Reconciliation.kind).where(
                Reconciliation.application_id == app.id,
                Reconciliation.status == "OPEN",
                Reconciliation.kind.not_in(["INTEGRITY", "SOURCE_CORRECTION", "SEPARATION"]),
            )
        )
    )
    for kind in kinds:
        resolve_case(db, app, kind, "APPLICATION_RELEASED_NO_EVIDENCE_OR_POLICY_DECISION")


def scoped_query(actor: Actor):  # type: ignore[no-untyped-def]
    query = select(Application)
    if set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        return query
    return query.where(
        or_(
            Application.person_id == actor.person.id,
            (Application.department_id.in_(actor.scopes) & (Application.state != "DRAFT")),
        )
    )


def lock_application(
    db: Session, app_id: UUID, actor: Actor | None = None
) -> tuple[Application, Offering]:
    # Global resource order: offering -> application -> mapping anchor -> sorted pools.
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(404, "APPLICATION_NOT_FOUND")
    if actor:
        can_read(actor, app)
    offering = db.scalar(
        select(Offering).where(Offering.id == app.offering_id).with_for_update(read=True)
    )
    app = db.scalar(
        select(Application)
        .where(Application.id == app_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    assert app and offering
    return app, offering


def check_version(app: Application, version: int) -> None:
    if app.version != version:
        raise HTTPException(409, "VERSION_CONFLICT")


def draft(db: Session, actor: Actor, key: UUID, body: DraftWrite) -> CommandResult:
    actor = common.refresh(db, actor, key)
    common.require_applicant(actor)
    op = f"APPLICATION_DRAFT:{body.id or 'NEW'}"
    if result := common.replay(db, actor, key, op, body):
        return result
    offering = db.get(Offering, body.offering_id)
    if not offering:
        raise HTTPException(404, "OFFERING_NOT_FOUND")
    if body.id:
        app, _ = lock_application(db, body.id, actor)
        if app.person_id != actor.person.id or app.state != "DRAFT":
            raise HTTPException(403, "OWN_DRAFT_REQUIRED")
        check_version(app, body.expected_version or 0)
        if app.offering_id != body.offering_id:
            raise HTTPException(409, "CREATE_NEW_DRAFT_FOR_DIFFERENT_OFFERING")
        app.version += 1
        app.declarations = body.declarations.model_dump()
    else:
        app = Application(
            id=uuid4(),
            person_id=actor.person.id,
            episode_id=actor.episode.id,
            department_id=actor.department.id,
            course_id=offering.course_id,
            offering_id=offering.id,
            declarations=body.declarations.model_dump(),
        )
        db.add(app)
        db.flush()
    db.add(
        DraftRevision(
            application_id=app.id,
            version=app.version,
            actor_id=actor.person.id,
            declarations=app.declarations,
        )
    )
    return common.finish(
        db, actor, key, op, body, app.id, {"declarations": app.declarations}, app.department_id
    )


def prior_gate(db: Session, app: Application) -> list[str]:
    from akus.applications import outcomes

    attempts = outcomes.assert_repeat_eligible(db, app)
    # An actual enrollment assertion on another run is a known prior attempt,
    # even if its application was later rejected or never progressed beyond draft.
    enrolled_runs = db.scalars(
        select(Application.offering_id)
        .join(EnrollmentClaim, EnrollmentClaim.application_id == Application.id)
        .where(
            Application.person_id == app.person_id,
            Application.course_id == app.course_id,
            Application.offering_id != app.offering_id,
        )
        .distinct()
    )
    if any(
        run not in attempts or not outcomes.conclusive_no_cert(db, attempts[run])
        for run in enrolled_runs
    ):
        raise HTTPException(423, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29")
    previous = list(
        db.scalars(
            select(Application).where(
                Application.person_id == app.person_id,
                Application.course_id == app.course_id,
                Application.id != app.id,
                Application.state != "DRAFT",
            )
        )
    )
    if any(p.state in {"UNDER_REVIEW", "APPROVED"} for p in previous):
        raise HTTPException(409, "ACTIVE_CANONICAL_COURSE_APPLICATION_EXISTS")
    # Every counted or past-exam prior run needs its own conclusive HoD finding.
    for p in previous:
        attempt = attempts.get(p.offering_id)
        if attempt and outcomes.conclusive_no_cert(db, attempt):
            continue
        previous_submission = db.get(Submission, p.id)
        if previous_submission:
            exam = previous_submission.facts.get("metadata", {}).get("scheduled_exam_on")
            if exam and date.fromisoformat(exam) <= today():
                raise HTTPException(423, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29")
        allocation = db.get(Allocation, p.id)
        if allocation and allocation.state != "RELEASED":
            raise HTTPException(423, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29")
    if app.declarations["prior_attempt"] == "VALID_CERTIFICATE":
        raise HTTPException(409, "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28")
    if app.declarations["prior_attempt"] != "NONE_DECLARED" and not attempts:
        raise HTTPException(423, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29")
    return [
        str(finding.id)
        for attempt in attempts.values()
        if (finding := outcomes.latest_finding(db, attempt.id))
        and finding.outcome == "NO_VALID_CERT"
    ]


def submit(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: Submit, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    common.require_applicant(actor)
    op = f"APPLICATION_SUBMITTED:{app_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    app, offering = lock_application(db, app_id, actor)
    if app.person_id != actor.person.id or app.state != "DRAFT":
        raise HTTPException(403, "OWN_DRAFT_REQUIRED")
    check_version(app, body.expected_version)
    from akus.exceptions.service import active_order

    if active_order(db, app):
        raise HTTPException(423, "PERMANENT_DEPARTURE_REQUIRES_NEW_EPISODE")
    if app.episode_id != actor.episode.id or app.department_id != actor.department.id:
        raise HTTPException(423, "SOURCE_CHANGE_REQUIRES_NEW_DRAFT")
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
        {"key": f"canonical:{app.person_id}:{app.course_id}"},
    )
    prior_findings = prior_gate(db, app)
    d = app.declarations
    if not str(d.get("academic_relevance", "")).strip():
        raise HTTPException(422, "ACADEMIC_RELEVANCE_REQUIRED")
    from akus.applications import participation

    if participation.known_enrollment(db, app):
        raise HTTPException(409, "NPTEL_FIRST_ENROLLMENT_PROHIBITED_Q21")
    if not d["score_sharing_yes"] or not d["acknowledgement"]:
        raise HTTPException(422, "SCORE_SHARING_AND_DECLARATIONS_REQUIRED")
    if not d["not_yet_enrolled"]:
        raise HTTPException(409, "NPTEL_FIRST_ENROLLMENT_PROHIBITED_Q21")
    if d["emerging_technology_exception"]:
        raise HTTPException(423, "EMERGING_TECH_AUTHORITY_POLICY_PENDING")
    source = snapshot(db, offering)
    if not source or offering.source_status != "CURRENT" or not source_usable(source, cfg):
        raise HTTPException(409, "SOURCE_MISSING_STALE_OR_UNAVAILABLE")
    if source.id != body.snapshot_id:
        raise HTTPException(409, "PROVIDER_SNAPSHOT_CHANGED")
    metadata = source.metadata_json
    required = [
        "duration_weeks",
        "starts_on",
        "ends_on",
        "enrollment_ends_on",
        "exam_registration_ends_on",
        "scheduled_exam_on",
    ]
    if any(metadata.get(k) is None for k in required):
        raise HTTPException(423, "VERIFIED_PROVIDER_DATES_REQUIRED")
    if today() >= date.fromisoformat(metadata["starts_on"]) and db.scalar(
        select(Application.id)
        .where(
            Application.person_id == app.person_id,
            Application.offering_id == app.offering_id,
            Application.state == "WITHDRAWN",
        )
        .limit(1)
    ):
        raise HTTPException(409, "REAPPLICATION_AFTER_COMMENCEMENT_PROHIBITED_Q25")
    if today() > date.fromisoformat(metadata["enrollment_ends_on"]) or today() > date.fromisoformat(
        metadata["exam_registration_ends_on"]
    ):
        raise HTTPException(409, "EXTERNAL_DEADLINE_CLOSED")
    if date.fromisoformat(metadata["scheduled_exam_on"]) < today():
        raise HTTPException(409, "SCHEDULED_EXAM_ALREADY_PAST")
    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.starts_on <= date.fromisoformat(metadata["scheduled_exam_on"]),
            AcademicYear.ends_on >= date.fromisoformat(metadata["scheduled_exam_on"]),
        )
    )
    if not year:
        raise HTTPException(423, "SCHEDULED_EXAM_YEAR_NOT_CONFIGURED")
    anchor = db.scalar(
        select(MappingAnchor)
        .where(
            MappingAnchor.department_id == app.department_id,
            MappingAnchor.course_id == app.course_id,
        )
        .with_for_update(read=True)
    )
    mapping = current_mapping(db, app.department_id, app.course_id) if anchor else None
    if not mapping:
        raise HTTPException(409, "HOD_MAPPING_REQUIRED")
    if mapping.id != body.mapping_revision_id:
        raise HTTPException(409, "PRIMARY_TOPIC_MAPPING_CHANGED")
    if mapping.topic_id not in topic_candidates(db, source):
        raise HTTPException(423, "PROVIDER_TAXONOMY_REVIEW_REQUIRED")
    pool = db.scalar(
        select(QuotaPool)
        .where(
            QuotaPool.department_id == app.department_id,
            QuotaPool.topic_id == mapping.topic_id,
            QuotaPool.academic_year_id == year.id,
        )
        .with_for_update()
    )
    if not pool or pool.status != "PUBLISHED":
        raise HTTPException(409, "PUBLISHED_ANNUAL_QUOTA_REQUIRED")
    if pool.occupied >= pool.maximum:
        raise HTTPException(409, "QUOTA_FULL")
    now = datetime.now(UTC)
    route = ["HOD"] if "DRC_HEAD" in actor.roles else ["DRC_HEAD", "HOD"]
    app.state, app.next_office, app.submitted_at = "UNDER_REVIEW", route[0], now
    app.version += 1
    db.add(
        Submission(
            application_id=app.id,
            snapshot_id=source.id,
            mapping_revision_id=mapping.id,
            original_pool_id=pool.id,
            submitted_at=now,
            facts={
                "metadata": metadata,
                "source_url": source.source_url,
                "digest": source.digest,
                "observed_at": source.observed_at.isoformat(),
                "trust": source.trust,
                "course_id": str(app.course_id),
                "offering_id": str(offering.id),
                "topic_id": str(mapping.topic_id),
                "mapping_version": mapping.version,
                "department_id": str(app.department_id),
                "academic_year": year.label,
                "policy": "V2.4/V2.3;Q02,Q21,Q27-Q29",
                "route": route,
                "prior_outcome_finding_ids": prior_findings,
                "roles": actor.roles,
                "declarations": d,
                "external_participation": "DECLARED_NOT_ENROLLED_NOT_PROVIDER_VERIFIED",
            },
        )
    )
    db.add(
        Allocation(
            application_id=app.id, pool_id=pool.id, state="HELD", schedule_snapshot_id=source.id
        )
    )
    pool.occupied += 1
    db.add(
        Ledger(
            movement_id=uuid4(),
            application_id=app.id,
            pool_id=pool.id,
            delta=1,
            kind="RESERVE",
            snapshot_id=source.id,
            actor_id=actor.person.id,
        )
    )
    notice(
        db,
        app,
        "APPLICATION_SUBMITTED",
        {"next_office": app.next_office, "pool_id": str(pool.id), "allocation": "HELD"},
    )
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        {
            "pool_id": str(pool.id),
            "snapshot_id": str(source.id),
            "mapping_revision_id": str(mapping.id),
            "route": route,
        },
        app.department_id,
    )


def applicant_still_eligible(db: Session, app: Application) -> bool:
    person, episode = db.get(Person, app.person_id), db.get(EmploymentEpisode, app.episode_id)
    now = datetime.now(UTC)
    office = db.scalar(
        select(OfficeAppointment.id).where(
            OfficeAppointment.person_id == app.person_id,
            OfficeAppointment.superseded.is_(False),
            OfficeAppointment.office.in_(["HOD", "ACTING_HOD", "PRINCIPAL"]),
            OfficeAppointment.valid_from <= now,
            or_(OfficeAppointment.valid_until.is_(None), OfficeAppointment.valid_until > now),
        )
    )
    department = db.scalar(
        select(DepartmentAssignment.department_id).where(
            DepartmentAssignment.episode_id == app.episode_id,
            DepartmentAssignment.starts_on <= today(),
            or_(
                DepartmentAssignment.ends_before.is_(None),
                DepartmentAssignment.ends_before > today(),
            ),
        )
    )
    return bool(
        person
        and person.enabled
        and episode
        and episode.is_faculty
        and episode.starts_on <= today()
        and (not episode.ends_before or episode.ends_before > today())
        and not office
        and department == app.department_id
    )


def queue_recheck(db: Session, pool: QuotaPool) -> None:
    """Notify seats waiting for capacity in this exact department/topic/year."""
    if pool.status != "PUBLISHED" or pool.occupied >= pool.maximum:
        return
    year = db.get(AcademicYear, pool.academic_year_id)
    assert year
    wanted = Reconciliation.context["scheduled_exam_on"].astext
    waiting = (
        select(Reconciliation.application_id)
        .join(Allocation, Allocation.application_id == Reconciliation.application_id)
        .join(QuotaPool, QuotaPool.id == Allocation.pool_id)
        .where(
            Reconciliation.status == "OPEN",
            Reconciliation.kind == "QUOTA_TRANSFER",
            Reconciliation.reason.in_(
                [
                    "TARGET_YEAR_NOT_CONFIGURED",
                    "TARGET_QUOTA_MISSING",
                    "TARGET_QUOTA_UNPUBLISHED",
                    "TARGET_QUOTA_FULL",
                ]
            ),
            Allocation.state.in_(["HELD", "CONFIRMED"]),
            QuotaPool.department_id == pool.department_id,
            QuotaPool.topic_id == pool.topic_id,
            or_(
                Reconciliation.context["target_pool_id"].astext == str(pool.id),
                wanted.between(year.starts_on.isoformat(), year.ends_on.isoformat()),
            ),
        )
    )
    for app_id in db.scalars(waiting):
        db.add(WorkJob(key=f"recheck:{app_id}:{uuid4()}", kind="QUOTA_RECHECK", state="PENDING"))


def release(
    db: Session, app: Application, actor: Actor | None, reason: str, retain: bool = False
) -> None:
    allocation = db.get(Allocation, app.id)
    if not allocation or allocation.state == "RELEASED":
        raise HTTPException(409, "COUNTED_ALLOCATION_REQUIRED")
    pool = db.scalar(select(QuotaPool).where(QuotaPool.id == allocation.pool_id).with_for_update())
    assert pool
    if not retain:
        pool.occupied -= 1
    allocation.state, allocation.version = (
        ("RETAINED" if retain else "RELEASED"),
        allocation.version + 1,
    )
    db.add(
        Ledger(
            movement_id=uuid4(),
            application_id=app.id,
            pool_id=pool.id,
            delta=0 if retain else -1,
            kind=reason,
            personal_schedule_id=allocation.personal_schedule_id,
            snapshot_id=allocation.schedule_snapshot_id,
            actor_id=actor.person.id if actor else None,
        )
    )
    if not retain:
        resolve_released_cases(db, app)
        queue_recheck(db, pool)
    notice(db, app, reason, {"pool_id": str(pool.id), "allocation": allocation.state})


def review(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: Review, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    op = f"APPLICATION_REVIEW:{app_id}"
    app, offering = lock_application(db, app_id, actor)
    if app.person_id == actor.person.id:
        raise HTTPException(403, "SELF_REVIEW_PROHIBITED")
    offices = [
        o
        for o in actor.offices
        if o.department_id == app.department_id
        and (o.office == app.next_office or app.next_office == "HOD" and o.office == "ACTING_HOD")
    ]
    # A retry after stage advancement may replay only for this original actor.
    if result := common.replay(db, actor, key, op, body):
        return result
    if not offices:
        raise HTTPException(403, "CURRENT_REVIEW_OFFICE_REQUIRED")
    check_version(app, body.expected_version)
    if app.state != "UNDER_REVIEW":
        raise HTTPException(409, "APPLICATION_NOT_UNDER_REVIEW")
    from akus.exceptions.service import active_order

    if active_order(db, app):
        raise HTTPException(423, "PERMANENT_SEPARATION_REVIEW_REQUIRED")
    if not applicant_still_eligible(db, app):
        raise HTTPException(423, "APPLICANT_SOURCE_CHANGE_POLICY_PENDING")
    if body.enrollment_extension and (app.next_office != "HOD" or body.decision != "APPROVE"):
        raise HTTPException(403, "EXTENSION_REQUIRES_FINAL_HOD_APPROVAL")
    if body.decision == "APPROVE":
        from akus.applications import participation

        participation.assert_review_chronology(db, app)
        prior_gate(db, app)
        source = snapshot(db, offering)
        if not source or offering.source_status != "CURRENT" or not source_usable(source, cfg):
            raise HTTPException(423, "CURRENT_PROVIDER_SOURCE_REQUIRED")
        deadline = source.metadata_json.get("enrollment_ends_on")
        if not deadline:
            raise HTTPException(423, "VERIFIED_PROVIDER_DATES_REQUIRED")
        submitted = db.get(Submission, app.id)
        original = submitted.facts["metadata"]["enrollment_ends_on"] if submitted else None
        cutoff_passed = any(
            day and today() > date.fromisoformat(day) for day in (original, deadline)
        )
        # DRC may complete its academic step. Only the current final HoD can
        # authenticate a still-open extension for this exact application.
        if cutoff_passed and app.next_office == "HOD" and not participation.verified_after(db, app):
            if not body.enrollment_extension or body.enrollment_extension.valid_through < today():
                raise HTTPException(423, "VERIFIED_LATE_ENROLLMENT_PATH_REQUIRED_Q19")
        if app.next_office == "DRC_HEAD":
            app.next_office = "HOD"
        else:
            app.state, app.next_office = "APPROVED", None
            allocation = db.get(Allocation, app.id)
            assert allocation and allocation.state == "HELD"
            allocation.state, allocation.version = "CONFIRMED", allocation.version + 1
    else:
        release(db, app, actor, "REJECT")
        app.state, app.next_office = "REJECTED", None
    db.add(
        ReviewDecision(
            application_id=app.id,
            actor_id=actor.person.id,
            office_id=offices[0].id,
            stage=offices[0].office,
            decision=body.decision,
            facts=body.model_dump(mode="json"),
        )
    )
    app.version += 1
    notice(
        db,
        app,
        "REVIEW_RECORDED",
        {
            "decision": body.decision,
            "office_id": str(offices[0].id),
            "state": app.state,
            "next_office": app.next_office,
        },
    )
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        {
            "decision": body.decision,
            "office_id": str(offices[0].id),
            "reason": body.reason,
            "source_reference": body.source_reference,
        },
        app.department_id,
    )


def verified_commencement(db: Session, offering: Offering, cfg: Settings) -> ProviderSnapshot:
    """Use accepted commencement, rejecting any newer conflicting start-date evidence.

    Caller holds the offering lock, so source acceptance and observation cannot race
    this decision. An exam-only conflict must not prevent lawful pre-start release;
    it still blocks new admission and requires separate schedule reconciliation.
    """
    source = snapshot(db, offering)
    if not source or not source_usable(source, cfg) or not source.metadata_json.get("starts_on"):
        raise HTTPException(423, "VERIFIED_COMMENCEMENT_REQUIRED")
    if offering.source_status == "SOURCE_CONFLICT_REVIEW_REQUIRED":
        pending = select(ProviderSnapshot.id).where(
            ProviderSnapshot.offering_id == offering.id,
            ProviderSnapshot.id != source.id,
            ProviderSnapshot.observed_at >= source.observed_at,
        )
        conflict = pending.where(
            ProviderSnapshot.metadata_json["starts_on"].astext.is_distinct_from(
                source.metadata_json["starts_on"]
            )
        )
        if db.scalar(pending.limit(1)) is None or db.scalar(conflict.limit(1)) is not None:
            raise HTTPException(423, "VERIFIED_COMMENCEMENT_REQUIRED")
    elif offering.source_status != "CURRENT":
        raise HTTPException(423, "VERIFIED_COMMENCEMENT_REQUIRED")
    return source


def withdraw(
    db: Session, actor: Actor, key: UUID, app_id: UUID, body: Withdraw, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    op = f"APPLICATION_WITHDRAWN:{app_id}"
    app, offering = lock_application(db, app_id, actor)
    if app.person_id != actor.person.id:
        raise HTTPException(403, "OWN_APPLICATION_REQUIRED")
    if result := common.replay(db, actor, key, op, body):
        return result
    check_version(app, body.expected_version)
    if app.state not in {"UNDER_REVIEW", "APPROVED"}:
        raise HTTPException(409, "ACTIVE_APPLICATION_REQUIRED")
    if not applicant_still_eligible(db, app):
        raise HTTPException(423, "APPLICANT_SOURCE_CHANGE_POLICY_PENDING")
    if db.scalar(
        select(Reconciliation.id).where(
            Reconciliation.application_id == app.id,
            Reconciliation.kind == "INTEGRITY",
            Reconciliation.status == "OPEN",
        )
    ):
        raise HTTPException(423, "INTEGRITY_AUTHORITY_POLICY_PENDING")
    source = verified_commencement(db, offering, cfg)
    retain = today() >= date.fromisoformat(source.metadata_json["starts_on"])
    from akus.applications import participation

    if not retain and (
        not body.not_enrolled_declaration or participation.known_enrollment(db, app)
    ):
        raise HTTPException(423, "HOD_VERIFIED_WITHDRAWAL_REQUIRED_Q04")
    release(db, app, actor, "WITHDRAW_RETAIN" if retain else "WITHDRAW_RELEASE", retain)
    app.state, app.next_office, app.version = "WITHDRAWN", None, app.version + 1
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        app.id,
        body.model_dump(mode="json")
        | {
            "counted": retain,
            "commencement_snapshot_id": str(source.id),
            "commencement_digest": source.digest,
            "starts_on": source.metadata_json["starts_on"],
        },
        app.department_id,
    )
