from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.catalog import common, provider
from akus.catalog.models import (
    Course,
    MappingAnchor,
    MappingRequest,
    MappingRevision,
    Offering,
    ProviderFetch,
    ProviderSnapshot,
    Topic,
    TopicAlias,
    TopicProposal,
)
from akus.catalog.schemas import (
    AliasWrite,
    CourseWrite,
    DemoOffering,
    MappingIntake,
    MappingWrite,
    OfferingFetch,
    ProposalResolve,
    ProposalWrite,
    SnapshotAccept,
    TopicWrite,
)
from akus.config import Settings
from akus.people.models import Department
from akus.people.schemas import CommandResult
from akus.people.service import require_admin


def get_course(db: Session, course_id: UUID) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "COURSE_NOT_FOUND")
    return course


def snapshot(db: Session, offering: Offering) -> ProviderSnapshot | None:
    return (
        db.get(ProviderSnapshot, offering.current_snapshot_id)
        if offering.current_snapshot_id
        else None
    )


def source_usable(record: ProviderSnapshot | None, cfg: Settings) -> bool:
    return bool(
        record
        and record.observed_at + timedelta(seconds=cfg.nptel_snapshot_max_age_seconds)
        > datetime.now(UTC)
        and (record.trust == "OFFICIAL_HTTPS" or cfg.demo_enabled and record.trust == "LOCAL_DEMO")
    )


def write_course(db: Session, actor: Actor, key: UUID, body: CourseWrite) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    op = f"COURSE_SOURCE:{body.id or 'NEW'}"
    if result := common.replay(db, actor, key, op, body):
        return result
    course = (
        db.scalar(select(Course).where(Course.id == body.id).with_for_update()) if body.id else None
    )
    if body.id:
        if not course:
            raise HTTPException(404, "COURSE_NOT_FOUND")
        if course.version != body.expected_version:
            raise HTTPException(409, "VERSION_CONFLICT")
        if course.code != body.code:
            raise HTTPException(423, "CANONICAL_IDENTITY_MERGE_POLICY_PENDING")
        before = {
            "title": course.title,
            "description": course.description,
            "version": course.version,
        }
        course.version += 1
        course.title, course.description, course.source_reference = (
            body.title,
            provider.plain(body.description),
            body.source_reference,
        )
    else:
        before = None
        course = Course(
            id=uuid4(),
            code=body.code,
            title=body.title,
            description=provider.plain(body.description),
            source_reference=body.source_reference,
        )
        db.add(course)
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        course.id,
        {"before": before, "after": body.model_dump(mode="json")},
    )


def record_fetch(
    db: Session,
    actor: Actor,
    key: UUID,
    body: OfferingFetch | DemoOffering,
    observation: provider.Observation | None,
    error: str | None = None,
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    get_course(db, body.course_id)
    op = "PROVIDER_OBSERVATION"
    if result := common.replay(db, actor, key, op, body):
        return result
    # Canonical identity association is an explicit source command, never title matching.
    db.execute(
        insert(Offering)
        .values(
            id=uuid4(),
            course_id=body.course_id,
            provider_id=body.provider_id,
            version=0,
            source_status="NOT_CHECKED",
        )
        .on_conflict_do_nothing(index_elements=["provider_id"])
    )
    offering = db.scalar(
        select(Offering).where(Offering.provider_id == body.provider_id).with_for_update()
    )
    assert offering
    if offering.course_id != body.course_id:
        raise HTTPException(409, "OFFERING_CANONICAL_IDENTITY_CONFLICT")
    now = observation.observed_at if observation else datetime.now(UTC)
    record = None
    if observation:
        record = ProviderSnapshot(
            id=uuid4(),
            offering_id=offering.id,
            digest=observation.digest,
            source_url=observation.source_url,
            trust="LOCAL_DEMO" if isinstance(body, DemoOffering) else "OFFICIAL_HTTPS",
            observed_at=observation.observed_at,
            metadata_json=observation.metadata.model_dump(mode="json"),
            actor_id=actor.person.id,
        )
        db.add(record)
        db.flush()
    db.add(
        ProviderFetch(
            offering_id=offering.id,
            actor_id=actor.person.id,
            observed_at=now,
            status="OBSERVED" if record else "UNAVAILABLE",
            error_code=error,
            snapshot_id=record.id if record else None,
        )
    )
    if not record:
        offering.source_status = "UNAVAILABLE"
    elif not offering.current_snapshot_id:
        offering.source_status = "AWAITING_SOURCE_ACCEPTANCE"
    else:
        accepted = snapshot(db, offering)
        if accepted and record.metadata_json != accepted.metadata_json:
            offering.source_status = "SOURCE_CONFLICT_REVIEW_REQUIRED"
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        offering.id,
        {
            "snapshot_id": str(record.id) if record else None,
            "status": "OBSERVED" if record else error,
            "reason": body.reason,
        },
    )


def local_observation(body: DemoOffering) -> provider.Observation:
    raw = body.metadata.model_dump_json().encode()
    return provider.Observation(
        body.metadata,
        sha256(raw).hexdigest(),
        f"local-demo://{body.provider_id}",
        datetime.now(UTC),
    )


def accept_snapshot(
    db: Session, actor: Actor, key: UUID, offering_id: UUID, body: SnapshotAccept, cfg: Settings
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    op = f"PROVIDER_ACCEPTED:{offering_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    offering = db.scalar(select(Offering).where(Offering.id == offering_id).with_for_update())
    if not offering:
        raise HTTPException(404, "OFFERING_NOT_FOUND")
    if body.expected_version != offering.version:
        raise HTTPException(409, "VERSION_CONFLICT")
    incoming = db.get(ProviderSnapshot, body.snapshot_id)
    if not incoming or incoming.offering_id != offering.id:
        raise HTTPException(422, "SNAPSHOT_OFFERING_MISMATCH")
    if not source_usable(incoming, cfg):
        raise HTTPException(409, "SOURCE_STALE_OR_UNTRUSTED")
    old = snapshot(db, offering)
    latest = db.scalar(
        select(ProviderSnapshot)
        .where(ProviderSnapshot.offering_id == offering.id)
        .order_by(ProviderSnapshot.observed_at.desc())
        .limit(1)
    )
    if (old and incoming.observed_at < old.observed_at) or (
        latest and incoming.observed_at < latest.observed_at
    ):
        raise HTTPException(409, "STALE_PROVIDER_EVENT")
    offering.current_snapshot_id, offering.source_status = incoming.id, "CURRENT"
    offering.version += 1
    from akus.applications.transfers import schedule_accepted

    schedule_accepted(db, offering, actor)
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        offering.id,
        {
            "previous_snapshot_id": str(old.id) if old else None,
            "snapshot_id": str(incoming.id),
            "source": incoming.source_url,
            "reason": body.reason,
            "version": offering.version,
        },
    )


def write_topic(db: Session, actor: Actor, key: UUID, body: TopicWrite) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    op = f"TOPIC_REFERENCE:{body.id or 'NEW'}"
    if result := common.replay(db, actor, key, op, body):
        return result
    topic = (
        db.scalar(select(Topic).where(Topic.id == body.id).with_for_update()) if body.id else None
    )
    if body.id:
        if not topic:
            raise HTTPException(404, "TOPIC_NOT_FOUND")
        if topic.version != body.expected_version:
            raise HTTPException(409, "VERSION_CONFLICT")
        if topic.code != body.code:
            raise HTTPException(423, "TOPIC_MERGE_POLICY_PENDING")
        topic.version += 1
        topic.name, topic.normalized_name, topic.source_reference = (
            body.name,
            common.normalize(body.name),
            body.source_reference,
        )
    else:
        topic = Topic(
            id=uuid4(),
            code=body.code,
            name=body.name,
            normalized_name=common.normalize(body.name),
            source_reference=body.source_reference,
        )
        db.add(topic)
    return common.finish(db, actor, key, op, body, topic.id, body.model_dump(mode="json"))


def write_alias(db: Session, actor: Actor, key: UUID, body: AliasWrite) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    if result := common.replay(db, actor, key, "TOPIC_ALIAS", body):
        return result
    if not db.get(Topic, body.topic_id):
        raise HTTPException(404, "TOPIC_NOT_FOUND")
    old = db.scalar(
        select(TopicAlias).where(TopicAlias.normalized_label == common.normalize(body.label))
    )
    if old and old.topic_id != body.topic_id:
        raise HTTPException(423, "TOPIC_ALIAS_COLLISION_POLICY_PENDING")
    record = old or TopicAlias(
        id=uuid4(),
        topic_id=body.topic_id,
        label=body.label,
        normalized_label=common.normalize(body.label),
        source_reference=body.source_reference,
    )
    db.add(record)
    return common.finish(
        db, actor, key, "TOPIC_ALIAS", body, record.id, body.model_dump(mode="json")
    )


def propose_topic(db: Session, actor: Actor, key: UUID, body: ProposalWrite) -> CommandResult:
    actor = common.refresh(db, actor, key)
    if not (actor.view().applicant_eligible or "HOD" in actor.roles):
        raise HTTPException(403, "TOPIC_INTAKE_ACCESS_DENIED")
    if result := common.replay(db, actor, key, "TOPIC_PROPOSED", body):
        return result
    db.execute(
        insert(TopicProposal)
        .values(
            id=uuid4(),
            department_id=actor.department.id,
            person_id=actor.person.id,
            normalized_label=common.normalize(body.label),
            source_reference=body.source_reference,
            reason=body.reason,
            status="PROPOSED",
        )
        .on_conflict_do_nothing(constraint="deduplicate_topic_proposal")
    )
    record = db.scalar(
        select(TopicProposal).where(
            TopicProposal.department_id == actor.department.id,
            TopicProposal.normalized_label == common.normalize(body.label),
        )
    )
    assert record
    return common.finish(
        db,
        actor,
        key,
        "TOPIC_PROPOSED",
        body,
        record.id,
        body.model_dump(mode="json"),
        actor.department.id,
    )


def resolve_proposal(
    db: Session, actor: Actor, key: UUID, proposal_id: UUID, body: ProposalResolve
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    require_admin(actor)
    op = f"TOPIC_PROPOSAL_RESOLVED:{proposal_id}"
    if result := common.replay(db, actor, key, op, body):
        return result
    record = db.scalar(
        select(TopicProposal).where(TopicProposal.id == proposal_id).with_for_update()
    )
    if not record or not db.get(Topic, body.topic_id):
        raise HTTPException(404, "NOT_FOUND")
    if record.topic_id and record.topic_id != body.topic_id:
        raise HTTPException(423, "TOPIC_MERGE_POLICY_PENDING")
    record.topic_id, record.status = body.topic_id, "REFERENCE_LINKED"
    return common.finish(
        db, actor, key, op, body, record.id, body.model_dump(mode="json"), record.department_id
    )


def mapping_anchor(
    db: Session, department: UUID, course: UUID, *, read: bool = False
) -> MappingAnchor:
    get_course(db, course)
    if not db.get(Department, department):
        raise HTTPException(404, "DEPARTMENT_NOT_FOUND")
    db.execute(
        insert(MappingAnchor)
        .values(id=uuid4(), department_id=department, course_id=course, version=0)
        .on_conflict_do_nothing(constraint="one_department_course_mapping")
    )
    row = db.scalar(
        select(MappingAnchor)
        .where(MappingAnchor.department_id == department, MappingAnchor.course_id == course)
        .with_for_update(read=read)
    )
    assert row
    return row


def current_mapping(db: Session, department: UUID, course: UUID) -> MappingRevision | None:
    return db.scalar(
        select(MappingRevision)
        .join(MappingAnchor, MappingAnchor.id == MappingRevision.mapping_id)
        .where(
            MappingAnchor.department_id == department,
            MappingAnchor.course_id == course,
            MappingRevision.valid_until.is_(None),
        )
    )


def request_mapping(db: Session, actor: Actor, key: UUID, body: MappingIntake) -> CommandResult:
    actor = common.refresh(db, actor, key)
    common.require_applicant(actor)
    if result := common.replay(db, actor, key, "MAPPING_REQUESTED", body):
        return result
    offering = db.get(Offering, body.offering_id)
    if not offering or not offering.current_snapshot_id:
        raise HTTPException(409, "OFFICIAL_SOURCE_REQUIRED")
    db.execute(
        insert(MappingRequest)
        .values(
            id=uuid4(),
            department_id=actor.department.id,
            course_id=offering.course_id,
            snapshot_id=offering.current_snapshot_id,
            requested_by=actor.person.id,
            status="REVIEW_PENDING",
            reason=body.reason,
        )
        .on_conflict_do_nothing(constraint="deduplicate_mapping_request")
    )
    record = db.scalar(
        select(MappingRequest).where(
            MappingRequest.department_id == actor.department.id,
            MappingRequest.course_id == offering.course_id,
            MappingRequest.snapshot_id == offering.current_snapshot_id,
        )
    )
    assert record
    return common.finish(
        db,
        actor,
        key,
        "MAPPING_REQUESTED",
        body,
        record.id,
        {"reason": body.reason, "reservation": "NONE"},
        actor.department.id,
    )


def topic_candidates(db: Session, record: ProviderSnapshot) -> list[UUID]:
    categories = [common.normalize(v) for v in record.metadata_json["categories"]]
    ids = list(
        db.scalars(select(TopicAlias.topic_id).where(TopicAlias.normalized_label.in_(categories)))
    )
    ids += list(db.scalars(select(Topic.id).where(Topic.normalized_name.in_(categories))))
    return list(set(ids))


def write_mapping(
    db: Session,
    actor: Actor,
    key: UUID,
    department: UUID,
    course: UUID,
    body: MappingWrite,
    cfg: Settings,
) -> CommandResult:
    actor = common.refresh(db, actor, key)
    office = common.require_hod(actor, department)
    op = f"PRIMARY_TOPIC_APPROVED:{department}:{course}"
    if result := common.replay(db, actor, key, op, body):
        return result
    record = db.get(ProviderSnapshot, body.snapshot_id)
    offering = (
        db.scalar(
            select(Offering).where(Offering.id == record.offering_id).with_for_update(read=True)
        )
        if record
        else None
    )
    if (
        not offering
        or offering.course_id != course
        or offering.current_snapshot_id != body.snapshot_id
    ):
        raise HTTPException(409, "CURRENT_COURSE_SOURCE_REQUIRED")
    if not source_usable(record, cfg) or offering.source_status != "CURRENT":
        raise HTTPException(409, "SOURCE_STALE_OR_UNTRUSTED")
    assert record
    if body.topic_id not in topic_candidates(db, record):
        raise HTTPException(422, "TOPIC_NOT_SUPPORTED_BY_PROVIDER_CATEGORIES")
    anchor = mapping_anchor(db, department, course)
    if anchor.version != body.expected_version:
        raise HTTPException(409, "VERSION_CONFLICT")
    previous = current_mapping(db, department, course)
    now = datetime.now(UTC)
    if previous:
        previous.valid_until = now
        db.flush()
    anchor.version += 1
    revision = MappingRevision(
        id=uuid4(),
        mapping_id=anchor.id,
        version=anchor.version,
        topic_id=body.topic_id,
        snapshot_id=body.snapshot_id,
        actor_id=actor.person.id,
        office_id=office.id,
        valid_from=now,
        reason=body.reason,
        source_reference=body.source_reference,
    )
    db.add(revision)
    from akus.applications.transfers import mapping_changed

    mapping_changed(db, department, course)
    for request in db.scalars(
        select(MappingRequest).where(
            MappingRequest.department_id == department,
            MappingRequest.course_id == course,
            MappingRequest.status == "REVIEW_PENDING",
        )
    ):
        request.status = "DECIDED"
    return common.finish(
        db,
        actor,
        key,
        op,
        body,
        anchor.id,
        {
            "old_topic_id": str(previous.topic_id) if previous else None,
            "topic_id": str(body.topic_id),
            "revision_id": str(revision.id),
            "office_id": str(office.id),
            "reason": body.reason,
            "existing_allocation_effect": "POLICY_PENDING:P-NEW-11",
        },
        department,
    )
