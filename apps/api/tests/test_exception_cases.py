from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_admission import assert_balance, draft, observe, setup, submit
from test_catalog import SOURCE, post
from test_participation import proof, verified
from test_people import login

from akus.applications import service as apps
from akus.applications.models import Allocation, Application, Ledger, Reconciliation
from akus.exceptions import service
from akus.exceptions.models import Departure, IntegrityMandate, SeparationSnapshot
from akus.models import DemoIdentity
from akus.people.models import DepartmentAssignment, EmploymentEpisode, Person


@pytest.fixture(scope="module")
def settings(settings):
    """Preserve the six-identity seed contract in the ordinary suite. Departure
    races need committed source changes visible to independent PostgreSQL sessions.
    Keep this dedicated test DB and its audit history across runs.
    """
    import os
    from pathlib import Path
    from unittest.mock import patch

    from alembic import command
    from alembic.config import Config
    from psycopg import connect, sql
    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url)
    assert settings.env == "test" and url.database.endswith("_test")
    name = url.database.removesuffix("_test")[:36] + "_departures_test"
    admin = url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    with connect(admin, autocommit=True) as connection:
        if not connection.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    database_url = url.set(database=name).render_as_string(hide_password=False)
    with patch.dict(os.environ, {"AKUS_DATABASE_URL": database_url}):
        command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    return settings.model_copy(update={"database_url": database_url})


def faculty(db, s):
    k = "sep-" + uuid4().hex[:16]
    d = DemoIdentity(
        key=k, name="LOCAL_TEST permanent departure", role="FACULTY", department="LOCAL_TEST"
    )
    db.add(d)
    db.flush()
    p = Person(
        staff_key=k, display_name=d.name, source_reference="LOCAL_TEST", demo_identity_id=d.id
    )
    db.add(p)
    db.flush()
    e = EmploymentEpisode(
        person_id=p.id, starts_on=date(2020, 1, 1), is_faculty=True, source_reference="LOCAL_TEST"
    )
    db.add(e)
    db.flush()
    m = DepartmentAssignment(
        episode_id=e.id,
        department_id=UUID(s["dept"]),
        starts_on=e.starts_on,
        source_reference="LOCAL_TEST",
    )
    db.add(m)
    db.commit()
    return k, e, m


def sample(client, db, start, enrolled=False, next_year=False):
    from test_admission import target

    s = setup(client)
    if next_year:
        s["pool"] = target(client, s)
        s["data"]["scheduled_exam_on"] = "2027-07-15"
    h, d, b = observe(
        client,
        s | {"data": s["data"] | {"starts_on": start.isoformat()}},
        day=s["data"]["scheduled_exam_on"],
    )
    assert post(client, f"/admin/nptel/offerings/{d['id']}/accept", b, h).status_code == 200
    k, e, m = faculty(db, s)
    aid, h = draft(client, s, k)
    assert submit(client, aid, h).status_code == 200
    instant = datetime.now(UTC)
    if enrolled:
        ev = proof()
        assert post(client, f"/applications/{aid}/enrollment-claims", ev, h).status_code == 200
        verified(client, aid, ev)
    return s, aid, e, m, instant


def earlier_sample(client, db, monkeypatch, starts_on):
    class EarlierSubmission(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) - timedelta(days=3)

    # Clock the original synthetic submission separately from the later HR order.
    with monkeypatch.context() as earlier:
        earlier.setattr(apps, "datetime", EarlierSubmission)
        return sample(client, db, starts_on)


def register(client, db, e, m, day, at=None):
    m.ends_before = day
    db.flush()
    e.ends_before = day
    db.commit()
    h = login(client, "admin")
    b = SOURCE | {
        "document_digest": "b" * 64,
        "observed_at": datetime.now(UTC).isoformat(),
        "effective_on": day.isoformat(),
        "effective_at": at.isoformat() if at else None,
        "permanent_order_confirmed": True,
    }
    r = post(client, f"/admin/employment-episodes/{e.id}/permanent-separation", b, h)
    assert r.status_code == 200, r.text
    return UUID(r.json()["id"])


def dossier(client, db, aid, role="hod", kind="SEPARATION"):
    cid = db.scalar(
        select(Reconciliation.id).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == kind
        )
    )
    h = login(client, role)
    path = f"/{kind.lower()}-cases/{cid}"
    r = client.get("/api/v1" + path)
    assert r.status_code == 200, r.text
    return path, r.json(), h


def decision(d, finding):
    return SOURCE | {
        "finding": finding,
        "expected_event_id": d["events"][0]["id"],
        "document_digest": "c" * 64,
        "observed_at": datetime.now(UTC).isoformat(),
        "independently_checked": True,
    }


@pytest.mark.parametrize("pathway", ["Q43", "Q44", "Q45", "Q47", "UNKNOWN"])
def test_separation_branches_and_current_seat(client, db, settings, monkeypatch, pathway):
    day = apps.today()
    start = (
        day + timedelta(days=7)
        if pathway in {"Q43", "Q44", "UNKNOWN"}
        else day
        if pathway == "Q47"
        else day - timedelta(days=1)
    )
    s, aid, e, m, t = sample(client, db, start, pathway in {"Q43", "Q44"})
    sep = t if pathway == "Q43" else datetime.now(UTC) if pathway == "Q44" else None
    oid = register(client, db, e, m, day, sep)
    p, d, h = dossier(client, db, aid)
    if pathway == "UNKNOWN":
        assert d["reason"] == "ENROLLMENT_CHRONOLOGY_REQUIRED"
        assert_balance(db, s["pool"], 1)
        assert post(client, p + "/decision", decision(d, "INDETERMINATE"), h).status_code == 423
        return
    if pathway in {"Q44", "Q47"}:
        assert_balance(db, s["pool"], 1)
        assert d["status"] == "OPEN"
        body = decision(d, "Q44" if pathway == "Q44" else "INDETERMINATE")
        for role in ["admin", "principal", "drc", "acting-hod"]:
            denied = post(client, p + "/decision", body, login(client, role))
            assert denied.status_code == 403
        monkeypatch.setattr(apps, "today", lambda: start + timedelta(days=1))
        h = login(client, "hod")
        key = uuid4()
        r = post(client, p + "/decision", body, h, key)
        assert r.status_code == 200, r.text
        assert post(client, p + "/decision", body, h, key).json() == r.json()
        assert post(client, p + "/decision", body, h).status_code == 409
    assert_balance(db, s["pool"], 0)
    assert db.get(Application, UUID(aid)).state == "SEPARATED"
    assert db.get(Allocation, UUID(aid)).state == "RELEASED"
    assert db.get(SeparationSnapshot, oid)
    with client.app.state.sessions.begin() as c:
        service.process_order(c, c.get(Departure, oid), settings)
    assert (
        db.scalar(
            select(func.count())
            .select_from(Ledger)
            .where(Ledger.application_id == UUID(aid), Ledger.kind == pathway + "_RELEASE")
        )
        == 1
    )
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM exception_case_events WHERE case_id=:c"), {"c": d["id"]})
    db.rollback()


@pytest.mark.parametrize("disposition", ["INVALIDATE", "UPHOLD"])
def test_integrity_mandate_is_specific_and_conflict_free(client, db, disposition):
    from test_outcomes import approve, finding, record

    s = setup(client)
    attempt = record(client, s)
    assert finding(client, attempt)[0].status_code == 200
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    approve(client, aid)
    assert finding(client, attempt, "VALID_CERT")[0].status_code == 200
    p, d, h = dossier(client, db, aid, kind="INTEGRITY")
    b = decision(d, disposition)
    for role in ["hod", "principal", "admin", "faculty"]:
        assert post(client, p + "/decision", b, login(client, role)).status_code == 403
    for role in ["hod", "acting-hod"]:
        pid = UUID(client.get("/api/v1/me", headers=login(client, role)).json()["person_id"])
        db.add(
            IntegrityMandate(
                case_id=UUID(d["id"]),
                reviewer_id=pid,
                basis="LOCAL_TEST case-specific formally documented mandate",
                valid_from=datetime.now(UTC) - timedelta(hours=1),
                valid_until=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    db.commit()
    assert post(client, p + "/decision", b, login(client, "hod")).status_code == 403
    r = post(client, p + "/decision", b, login(client, "acting-hod"))
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 0 if disposition == "INVALIDATE" else 1)
    assert db.get(Application, UUID(aid)).state == (
        "INVALIDATED" if disposition == "INVALIDATE" else "APPROVED"
    )
    again = client.get("/api/v1" + p).json()
    assert again["status"] == "RESOLVED" and again["events"][0]["action"] == disposition


def test_reschedule_vs_permanent_separation_releases_once(client, db, settings):
    from test_admission import actor_token, parallel, target

    from akus.applications.models import Ledger
    from akus.catalog import service as catalog
    from akus.catalog.schemas import SnapshotAccept
    from akus.exceptions.schemas import Order

    day = apps.today()
    s, aid, e, m, _ = sample(client, db, day - timedelta(days=1))
    dest = target(client, s)
    _, off, body = observe(
        client, s | {"data": s["data"] | {"starts_on": (day - timedelta(days=1)).isoformat()}}
    )
    m.ends_before = day
    db.flush()
    e.ends_before = day
    db.commit()
    active = actor_token(client, "admin")
    results = parallel(
        client,
        [
            (
                active,
                lambda c, a: catalog.accept_snapshot(
                    c, a, uuid4(), UUID(off["id"]), SnapshotAccept.model_validate(body), settings
                ),
            ),
            (
                active,
                lambda c, a: service.record_order(
                    c,
                    a,
                    uuid4(),
                    e.id,
                    Order.model_validate(
                        SOURCE
                        | {
                            "document_digest": "a" * 64,
                            "observed_at": datetime.now(UTC),
                            "permanent_order_confirmed": True,
                            "effective_on": day,
                        }
                    ),
                    settings,
                ),
            ),
        ],
    )
    assert results == ["OK", "OK"]
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 0)
    assert (
        db.scalar(
            select(func.count())
            .select_from(Ledger)
            .where(Ledger.application_id == UUID(aid), Ledger.kind == "Q45_RELEASE")
        )
        == 1
    )


@pytest.mark.parametrize(
    "when,score",
    [
        ("BEFORE", 75),
        ("BEFORE", 88),
        ("BEFORE", 74),
        ("BEFORE", 79),
        ("BEFORE", 84),
        ("AFTER", 92),
        ("UNCERTAIN", 80),
    ],
)
def test_retrospective_evidence_preserves_as_of_and_seat(client, db, when, score):
    from test_outcomes import approve

    from akus.exceptions.models import HistoricalMandate
    from akus.sources.models import Subject, TeachingAssignment

    day = apps.today()
    s, aid, e, m, _ = sample(client, db, day - timedelta(days=4), True, next_year=score == 84)
    approve(client, aid)
    subj = Subject(
        code="S" + uuid4().hex, name="LOCAL_TEST archival teaching", source_reference="LOCAL_TEST"
    )
    db.add(subj)
    db.flush()
    from akus.models import AcademicYear

    first = day.replace(year=day.year - 2) - timedelta(days=1 if score == 79 else 0)
    anchor = first.year if first.month >= 7 else first.year - 1
    year = db.scalar(select(AcademicYear).where(AcademicYear.starts_on == date(anchor, 7, 1)))
    if not year:
        year = AcademicYear(
            label=f"{anchor}-{anchor + 1}",
            starts_on=date(anchor, 7, 1),
            ends_on=date(anchor + 1, 6, 30),
            source="LOCAL_TEST historical teaching",
        )
        db.add(year)
        db.flush()
    db.add(
        TeachingAssignment(
            external_key=uuid4().hex,
            episode_id=e.id,
            subject_id=subj.id,
            department_id=UUID(s["dept"]),
            academic_year_id=year.id,
            term="Local",
            starts_on=first,
            ends_before=first + timedelta(days=1),
            source_reference="LOCAL_TEST",
        )
    )
    db.commit()
    if score in (75, 84):
        from akus.exceptions.models import ArchivedObligation

        db.add(
            ArchivedObligation(
                episode_id=e.id,
                subject_id=subj.id,
                first_assignment=first,
                decided_on=first,
                decision_reference="LOCAL_TEST separately archived institutional ruling",
                authority_basis="LOCAL_TEST prior documented academic adjudication",
                document_digest="d" * 64,
            )
        )
        db.commit()
    exam = datetime.now(UTC)
    oid = register(client, db, e, m, day, datetime.now(UTC))
    if when == "AFTER":
        exam = datetime.now(UTC)
    path, d, _ = dossier(client, db, aid)
    route = path + "/historical-review"
    before = datetime.now(UTC)
    payload = SOURCE | {
        "document_digest": "a" * 64,
        "observed_at": before.isoformat(),
        "actual_exam_on": str(day),
        "actual_exam_at": None if when == "UNCERTAIN" else exam.isoformat(),
        "issued_on": str(day),
        "score_percent": score,
        "certificate_key": "LOCAL_TEST_" + uuid4().hex,
        "subject_id": str(subj.id),
        "relevance_basis": "Local subject-specific syllabus and assessed content match",
        "checked_person_offering_certificate": True,
        "verified_exam_and_score_sharing": True,
    }
    for role in ["hod", "admin", "principal", "drc"]:
        assert post(client, route, payload, login(client, role)).status_code == 403
    h = login(client, "acting-hod")
    reviewer = UUID(client.get("/api/v1/me").json()["person_id"])
    db.add(
        HistoricalMandate(
            case_id=UUID(d["id"]),
            reviewer_id=reviewer,
            subject_id=subj.id,
            basis="LOCAL_TEST exact case and subject mandate",
            valid_from=before - timedelta(hours=1),
            valid_until=before + timedelta(hours=1),
        )
    )
    db.commit()
    if score == 84:
        payload.update(subject_id=None, relevance_basis=None)
    key = uuid4()
    result = post(client, route, payload, h, key)
    assert result.status_code == 200, result.text
    assert post(client, route, payload, h, key).json() == result.json()
    assert post(client, route, payload, h).status_code == 409
    earlier = client.get("/api/v1" + route, params={"as_of": before.isoformat()}).json()
    assert earlier["finding"] is None and earlier["annual"] == {}
    later = client.get("/api/v1" + route).json()
    if score == 84:
        assert later["finding"]["silver"] == "RELEVANCE_UNASSESSED"
        earlier_subject = datetime.now(UTC)
        assessment = SOURCE | {
            "finding_id": result.json()["id"],
            "subject_id": str(subj.id),
            "checked_subject_relevance": True,
            "relevance_basis": "LOCAL_TEST exact subject evidence",
            "observed_at": earlier_subject.isoformat(),
            "document_digest": "e" * 64,
        }
        assert (
            post(client, route + "/subject", assessment, login(client, "principal")).status_code
            == 403
        )
        h = login(client, "acting-hod")
        assert post(client, route + "/subject", assessment, h).status_code == 200
        assert post(client, route + "/subject", assessment, h).status_code == 423
        assert (
            client.get("/api/v1" + route, params={"as_of": earlier_subject.isoformat()}).json()[
                "finding"
            ]["silver"]
            == "RELEVANCE_UNASSESSED"
        )
        later = client.get("/api/v1" + route).json()
    if when == "BEFORE":
        assert later["finding"]["eligibility"] == "ELIGIBLE"
        assert list(later["annual"].values()) == ["VERIFIED_FULFILLED"]
        assert later["finding"]["silver"] == (
            "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"
            if score == 88
            else "EXAM_AFTER_DEADLINE"
            if score == 79
            else "VERIFIED_ON_TIME"
            if score >= 75
            else "BELOW_SILVER_THRESHOLD"
        )
    else:
        assert later["annual"] == {}
        assert later["finding"]["eligibility"] == (
            "EXAM_NOT_BEFORE_SEPARATION" if when == "AFTER" else "SEPARATION_ORDER_UNCERTAIN"
        )
    assert (
        later["subjects"][0]["status_at_separation"]
        == earlier["subjects"][0]["status_at_separation"]
    )
    assert db.get(SeparationSnapshot, oid).subjects[0]["subject_id"] == str(subj.id)
    if score == 84:
        from starlette.exceptions import HTTPException

        from akus.applications.outcomes import assert_repeat_eligible
        from akus.sources.service import teaching_view

        old = db.scalar(select(TeachingAssignment).where(TeachingAssignment.episode_id == e.id))
        assert teaching_view(db, old)["compliance"] == "VERIFIED_ON_TIME"
        assert later["finding"]["subject_deadline"] == str(day)
        from akus.applications.models import Submission

        assert (
            db.get(Submission, UUID(aid)).facts["academic_year"]
            != later["finding"]["academic_year"]
        )
        rehire = EmploymentEpisode(
            person_id=e.person_id,
            starts_on=day,
            is_faculty=True,
            source_reference="LOCAL_TEST new employment",
        )
        db.add(rehire)
        db.flush()
        db.add(
            DepartmentAssignment(
                episode_id=rehire.id,
                department_id=UUID(s["dept"]),
                starts_on=day,
                source_reference="LOCAL_TEST",
            )
        )
        db.flush()
        new_teaching = TeachingAssignment(
            external_key=uuid4().hex,
            episode_id=rehire.id,
            subject_id=subj.id,
            department_id=UUID(s["dept"]),
            academic_year_id=UUID(s["year"]),
            term="Local",
            starts_on=day,
            ends_before=day + timedelta(days=7),
            source_reference="LOCAL_TEST",
        )
        db.add(new_teaching)
        db.flush()
        assert teaching_view(db, new_teaching)["first_official_date"] == day
        assert teaching_view(db, new_teaching)["status_at_separation"] is None
        candidate = Application(
            id=uuid4(),
            person_id=e.person_id,
            episode_id=rehire.id,
            course_id=UUID(s["course"]),
            state="DRAFT",
        )
        with pytest.raises(HTTPException, match="CANONICAL_COURSE_REPEAT_PROHIBITED_Q28"):
            assert_repeat_eligible(db, candidate)
    assert db.get(Application, UUID(aid)).state == "SEPARATED"
    assert_balance(db, s["pool"], 0)


def test_q43_authoritative_absence_is_separately_designated(client, db):
    from akus.exceptions.models import HistoricalMandate

    s, aid, ep, member, _ = sample(client, db, apps.today() + timedelta(days=4))
    effective = datetime.now(UTC)
    register(client, db, ep, member, apps.today(), effective)
    p, d, _ = dossier(client, db, aid)
    assert d["reason"] == "ENROLLMENT_CHRONOLOGY_REQUIRED"
    now = datetime.now(UTC)
    b = SOURCE | {
        "expected_event_id": d["events"][0]["id"],
        "observed_at": now.isoformat(),
        "absence_through": now.isoformat(),
        "document_digest": "a" * 64,
        "checked_complete_person_offering_roster": True,
    }
    h = login(client, "acting-hod")
    pid = UUID(client.get("/api/v1/me").json()["person_id"])
    grant = dict(
        case_id=UUID(d["id"]),
        reviewer_id=pid,
        basis="LOCAL_TEST narrow roster appointment",
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(hours=1),
    )
    db.add(HistoricalMandate(**grant, purpose="CERTIFICATE"))
    db.commit()
    assert post(client, p + "/roster-finding", b, h).status_code == 403
    db.add(HistoricalMandate(**grant, purpose="ENROLLMENT_ABSENCE"))
    db.commit()
    assert (
        post(
            client,
            p + "/roster-finding",
            b | {"absence_through": (effective - timedelta(seconds=1)).isoformat()},
            h,
        ).status_code
        == 423
    )
    key = uuid4()
    result = post(client, p + "/roster-finding", b, h, key)
    assert result.status_code == 200, result.text
    assert post(client, p + "/roster-finding", b, h, key).json() == result.json()
    assert_balance(db, s["pool"], 0)
    events = client.get("/api/v1" + p).json()["events"]
    assert [e["action"] for e in events[:2]] == ["Q43", "NON_ENROLLMENT_VERIFIED"]
    assert events[0]["actor"] is None and events[1]["actor"] == str(pid)


def test_vacant_hod_alerts_and_restoration_leave_counted_seat_unchanged(client, db):
    from akus.applications.models import AcademicNotice
    from akus.exceptions import reviewer
    from akus.people.models import OfficeAppointment

    s = setup(client)
    aid, h = draft(client, s, "drc")
    assert submit(client, aid, h).status_code == 200
    login(client, "principal")
    response = client.get("/api/v1/review-office-alerts", params={"vacant_only": False}).json()
    assert response["total"] >= 1
    app = db.get(Application, UUID(aid))
    initial = reviewer.sources(db, app)
    assert initial["status"] == "ASSIGNED" and initial["office"] == "HOD"
    office = db.get(OfficeAppointment, UUID(initial["appointment_id"]))
    person = db.get(Person, office.person_id)
    person.enabled = False
    db.flush()
    reviewer.notify_changes(db)
    db.flush()
    reviewer.notify_changes(db)
    db.flush()
    query = (
        select(AcademicNotice)
        .where(
            AcademicNotice.application_id == app.id, AcademicNotice.kind == "REVIEW_OFFICE_ALERT"
        )
        .order_by(AcademicNotice.created_at)
    )
    rows = db.scalars(query).all()
    assert (
        len(rows) == 1
        and rows[0].facts["status"] == "VACANT"
        and rows[0].facts["enrollment_cutoff"]
    )
    person.enabled = True
    db.flush()
    reviewer.notify_changes(db)
    db.flush()
    assert {n.facts["status"] for n in db.scalars(query)} == {"VACANT", "ASSIGNED"}
    assert db.get(Allocation, app.id).state == "HELD"
    db.rollback()


def test_rejection_vs_reschedule_releases_one_current_pool(client, db, settings):
    from test_admission import actor_token, parallel, target

    from akus.applications.schemas import Review
    from akus.catalog import service as catalog
    from akus.catalog.schemas import SnapshotAccept

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    destination = target(client, s)
    _, off, accept = observe(client, s)
    results = parallel(
        client,
        [
            (
                actor_token(client, "admin"),
                lambda c, a: catalog.accept_snapshot(
                    c, a, uuid4(), UUID(off["id"]), SnapshotAccept.model_validate(accept), settings
                ),
            ),
            (
                actor_token(client, "drc"),
                lambda c, a: apps.review(
                    c,
                    a,
                    uuid4(),
                    UUID(aid),
                    Review.model_validate(SOURCE | {"decision": "REJECT", "expected_version": 2}),
                    settings,
                ),
            ),
        ],
    )
    assert results == ["OK", "OK"]
    assert_balance(db, s["pool"], 0)
    assert_balance(db, destination, 0)
    allocation = db.get(Allocation, UUID(aid))
    assert allocation.state == "RELEASED"
    releases = db.scalars(
        select(Ledger).where(Ledger.application_id == UUID(aid), Ledger.kind == "REJECT")
    ).all()
    assert len(releases) == 1 and releases[0].pool_id == allocation.pool_id


def test_separation_after_completed_transfer_releases_destination_and_preserves_correction(
    client, db, settings
):
    from test_admission import reschedule, target

    s, aid, e, m, _ = sample(client, db, apps.today() - timedelta(days=2))
    s["data"]["starts_on"] = str(apps.today() - timedelta(days=2))
    dest = target(client, s)
    reschedule(client, s)
    assert_balance(db, dest, 1)
    oid = register(client, db, e, m, apps.today())
    assert_balance(db, dest, 0)
    release = db.scalar(
        select(Ledger).where(Ledger.application_id == UUID(aid), Ledger.kind == "Q45_RELEASE")
    )
    assert release.pool_id == UUID(dest)
    s["data"]["starts_on"] = str(apps.today() + timedelta(days=4))
    reschedule(client, s)
    with client.app.state.sessions.begin() as c:
        service.process_order(c, c.get(Departure, oid), settings)
    pending = db.scalar(
        select(Reconciliation).where(
            Reconciliation.kind == "SOURCE_CORRECTION", Reconciliation.application_id == UUID(aid)
        )
    )
    assert pending.status == "OPEN" and pending.reason == "RELEASED_SEAT_CORRECTION_POLICY_PENDING"
    from akus.applications import transfers

    with client.app.state.sessions.begin() as c:
        transfers.worker_recheck(c, UUID(aid))
    db.refresh(pending)
    assert pending.status == "OPEN"
    assert db.get(Application, UUID(aid)).state == "SEPARATED"
    assert_balance(db, dest, 0)
    assert_balance(db, s["pool"], 0)


def test_unresolved_same_day_chronology_and_unassessed_certificate_are_recoverable(
    client, db, monkeypatch
):
    """Also supplies synthetic, scoped dossiers to the isolated browser gate."""
    import json

    from test_outcomes import approve

    from akus.exceptions.models import HistoricalMandate

    day = apps.today()
    s, aid, e, m, _ = sample(client, db, day)
    register(client, db, e, m, day)
    _, pending, _ = dossier(client, db, aid)
    assert pending["reason"] == "Q47_CHRONOLOGY_REVIEW" and pending["can_decide"]
    assert_balance(db, s["pool"], 1)
    _, aid, e, m, _ = sample(client, db, day - timedelta(days=2), True)
    approve(client, aid)
    # Preserve a source instant strictly following the independently established
    # enrollment (browser datetime-local supports milliseconds).
    exam = datetime.now(UTC)
    exam = exam.replace(microsecond=(exam.microsecond // 1000) * 1000)
    register(client, db, e, m, day, datetime.now(UTC))
    path, d, _ = dossier(client, db, aid)
    login(client, "acting-hod")
    reviewer = UUID(client.get("/api/v1/me").json()["person_id"])
    db.add(
        HistoricalMandate(
            case_id=UUID(d["id"]),
            reviewer_id=reviewer,
            basis="LOCAL_TEST archived certificate mandate",
            valid_from=exam - timedelta(hours=1),
            valid_until=exam + timedelta(hours=2),
        )
    )
    db.commit()
    assert client.get("/api/v1" + path).json()["may_verify_certificate"]
    assert client.get("/api/v1" + path + "/historical-review").json()["finding"] is None
    s, aid, ep, member, _ = earlier_sample(client, db, monkeypatch, day + timedelta(days=3))
    register(client, db, ep, member, day)
    _, date_case, _ = dossier(client, db, aid)
    assert date_case["reason"] == "ENROLLMENT_CHRONOLOGY_REQUIRED" and date_case["can_decide"]
    assert_balance(db, s["pool"], 1)
    print(
        "LOCAL_PHASE5_BROWSER="
        + json.dumps(
            {
                "pending": pending["id"],
                "historical": d["id"],
                "date_only": date_case["id"],
                "enrolled_on": str(day - timedelta(days=1)),
                "exam_at": exam.isoformat(),
                "exam_on": str(day),
            }
        )
    )


@pytest.mark.parametrize("outcome", ["Q43", "Q44", "Q45"])
def test_same_day_documented_order_controls_closure(client, db, outcome):
    s, aid, e, m, submitted = sample(client, db, apps.today())
    register(client, db, e, m, apps.today())
    p, d, h = dossier(client, db, aid)
    # Ordered source instants inside the observed interval, in a LOCAL_TEST archive.
    interval = (datetime.now(UTC) - submitted) / 5
    first, second, third = (submitted + interval * n for n in (1, 2, 3))
    enrolled, dep, start = {
        "Q43": (third, first, second),
        "Q44": (first, second, third),
        "Q45": (first, third, second),
    }[outcome]
    b = decision(d, "AFTER_START" if outcome == "Q45" else "BEFORE_START") | {
        "enrollment_at": enrolled.isoformat(),
        "separation_at": dep.isoformat(),
        "commencement_at": start.isoformat(),
    }
    assert post(client, p + "/decision", b, h).status_code == 200
    assert client.get("/api/v1" + p).json()["events"][0]["action"] == outcome
    assert_balance(db, s["pool"], 0)


def test_future_permanent_order_until_effective_day(client, db, settings, monkeypatch):
    today = apps.today()
    s, aid, e, m, _ = sample(client, db, today - timedelta(days=2))
    oid = register(client, db, e, m, today + timedelta(days=1))
    assert db.get(SeparationSnapshot, oid) is None
    assert db.get(Application, UUID(aid)).state == "UNDER_REVIEW"
    assert_balance(db, s["pool"], 1)
    monkeypatch.setattr(apps, "today", lambda: today + timedelta(days=1))
    with client.app.state.sessions.begin() as c:
        service.process_order(c, c.get(Departure, oid), settings)
    assert db.get(SeparationSnapshot, oid)
    assert_balance(db, s["pool"], 0)


def test_historical_annual_pair_requires_distinct_canonical_courses_in_same_actual_year():
    from akus.exceptions.history import annual_standing

    four = {"academic_year": "2025–26", "duration_weeks": 4, "course_id": "A"}
    two = four | {"course_id": "B"}
    assert annual_standing([four, four]) == {"2025–26": "INSUFFICIENT_QUALIFYING_COURSES"}
    assert annual_standing([four, two]) == {"2025–26": "VERIFIED_FULFILLED"}
    assert set(annual_standing([four, two | {"academic_year": "2026–27"}]).values()) == {
        "INSUFFICIENT_QUALIFYING_COURSES"
    }
    assert annual_standing([four | {"duration_weeks": 6}, two | {"duration_weeks": 2}]) == {
        "2025–26": "INSUFFICIENT_QUALIFYING_COURSES"
    }


def test_hod_rotation_during_pending_review_preserves_drc_decision_and_seat(client, db, settings):
    from sqlalchemy.orm import Session
    from starlette.exceptions import HTTPException
    from test_admission import actor_token

    from akus.access import authority
    from akus.applications.schemas import Review
    from akus.applications.workflow_models import ReviewDecision
    from akus.exceptions import reviewer
    from akus.models import AuthSession
    from akus.people import service as people
    from akus.people.models import OfficeAppointment
    from akus.people.schemas import AppointmentCreate, AppointmentEnd

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    reviewpath = "/applications/" + aid + "/review"
    assert (
        post(
            client,
            reviewpath,
            SOURCE | {"decision": "APPROVE", "expected_version": 2},
            login(client, "drc"),
        ).status_code
        == 200
    )
    replacement, _, _ = faculty(db, s)
    tokens = {k: actor_token(client, k) for k in ("hod", "admin", "principal", replacement)}
    # Actual committed subcommands use savepoints on this single outer PG
    # transaction so other tests keep their effective source appointments.
    with client.app.state.engine.connect() as connection:
        outer = connection.begin()
        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as tx:

                def actor(key):
                    live = tx.get(AuthSession, tokens[key])
                    return authority(tx, tx.get(DemoIdentity, live.identity_id), live)

                app = tx.get(Application, UUID(aid))
                prior = tx.scalar(
                    select(ReviewDecision).where(ReviewDecision.application_id == app.id)
                )
                old = tx.get(OfficeAppointment, UUID(reviewer.sources(tx, app)["appointment_id"]))
                people.end_appointment(
                    tx,
                    actor("admin"),
                    uuid4(),
                    old.id,
                    AppointmentEnd(
                        expected_version=old.version,
                        reason="LOCAL_TEST documented end of appointment",
                    ),
                )
                assert reviewer.sources(tx, app)["status"] == "VACANT"
                body = Review.model_validate(
                    SOURCE | {"decision": "APPROVE", "expected_version": 3}
                )
                # Ending the appointment also removes the former HoD's dossier scope.
                # Institutional oversight retains read access during the vacancy.
                for role, denial in (
                    ("hod", "APPLICATION_ACCESS_DENIED"),
                    ("admin", "CURRENT_REVIEW_OFFICE_REQUIRED"),
                    ("principal", "CURRENT_REVIEW_OFFICE_REQUIRED"),
                ):
                    with pytest.raises(HTTPException) as denied:
                        apps.review(tx, actor(role), uuid4(), app.id, body, settings)
                    assert (denied.value.status_code, denied.value.detail) == (403, denial)
                    assert tx.get(Application, app.id).next_office == "HOD"
                assert tx.get(Allocation, app.id).state == "HELD"
                new = people.create_appointment(
                    tx,
                    actor("admin"),
                    uuid4(),
                    AppointmentCreate(
                        person_id=actor(replacement).person.id,
                        department_id=UUID(s["dept"]),
                        office="ACTING_HOD",
                        valid_from=datetime.now(UTC),
                        source_reference="LOCAL_TEST_ROTATION",
                        reason="Local effective appointment",
                    ),
                )
                assert reviewer.sources(tx, app)["appointment_id"] == str(new.id)
                apps.review(tx, actor(replacement), uuid4(), app.id, body, settings)
                assert tx.get(Application, app.id).state == "APPROVED"
                assert tx.get(Allocation, app.id).state == "CONFIRMED"
                decisions = tx.scalars(
                    select(ReviewDecision).where(ReviewDecision.application_id == app.id)
                ).all()
                assert {d.office_id for d in decisions} == {prior.office_id, new.id}
        finally:
            outer.rollback()


@pytest.mark.parametrize("disposition", ["INVALIDATE", "UPHOLD"])
def test_integrity_disposition_during_permanent_departure(client, db, settings, disposition):
    from test_outcomes import approve

    day = apps.today()
    s, aid, episode, member, _ = sample(client, db, day - timedelta(days=5))
    approve(client, aid)
    applicant = db.get(Person, episode.person_id)
    h = login(client, applicant.staff_key)
    evidence = proof(enrolled_at=(datetime.now(UTC) - timedelta(days=1)).isoformat())
    assert post(client, f"/applications/{aid}/enrollment-claims", evidence, h).status_code == 200
    verified(client, aid, evidence)
    order = register(client, db, episode, member, day)
    sep_path, sep, _ = dossier(client, db, aid)
    assert sep["reason"] == "CONCURRENT_INTEGRITY_POLICY_PENDING"
    assert_balance(db, s["pool"], 1)
    path, c, _ = dossier(client, db, aid, kind="INTEGRITY")
    h = login(client, "acting-hod")
    pid = UUID(client.get("/api/v1/me").json()["person_id"])
    db.add(
        IntegrityMandate(
            case_id=UUID(c["id"]),
            reviewer_id=pid,
            basis="LOCAL_TEST independent exact-case appointment",
            valid_from=datetime.now(UTC) - timedelta(hours=1),
            valid_until=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    db.commit()
    command = decision(c, disposition)
    key = uuid4()
    r = post(client, path + "/decision", command, h, key)
    assert r.status_code == 200, r.text
    assert post(client, path + "/decision", command, h, key).json() == r.json()
    assert_balance(db, s["pool"], 0 if disposition == "INVALIDATE" else 1)
    for _ in range(2):
        with client.app.state.sessions.begin() as tx:
            service.process_order(tx, tx.get(Departure, order), settings)
    login(client, "principal")
    closed = client.get("/api/v1" + sep_path).json()
    assert closed["status"] == "RESOLVED"
    if disposition == "INVALIDATE":
        assert closed["reason"] == "CLOSED_BY_INTEGRITY_INVALIDATION"
        assert closed["events"][0]["facts"]["integrity_case_id"] == c["id"]
        assert closed["events"][0]["facts"]["chronology"] == "UNADJUDICATED"
    else:
        assert closed["reason"] == "Q45"
    assert db.get(Application, UUID(aid)).state == (
        "INVALIDATED" if disposition == "INVALIDATE" else "SEPARATED"
    )
    assert_balance(db, s["pool"], 0)
    releases = db.scalars(
        select(Ledger.kind).where(Ledger.application_id == UUID(aid), Ledger.delta == -1)
    ).all()
    assert releases == ["INVALIDATE_RELEASE" if disposition == "INVALIDATE" else "Q45_RELEASE"]


@pytest.mark.parametrize("same_start", [False, True])
def test_late_date_only_enrollment_source_needs_no_invented_instant(
    client, db, monkeypatch, same_start
):
    day = apps.today()

    s, aid, ep, m, _ = earlier_sample(
        client, db, monkeypatch, day if same_start else day + timedelta(days=3)
    )
    register(client, db, ep, m, day)
    path, d, h = dossier(client, db, aid)
    b = decision(d, "BEFORE_START" if same_start else "Q44")
    if same_start:
        sep = datetime.now(UTC) - timedelta(minutes=2)
        b.update(
            separation_at=sep.isoformat(), commencement_at=(sep + timedelta(seconds=10)).isoformat()
        )
    assert post(client, path + "/decision", b | {"enrollment_on": str(day)}, h).status_code == 423
    assert_balance(db, s["pool"], 1)
    assert (
        post(
            client, path + "/decision", b | {"enrollment_on": str(day - timedelta(days=1))}, h
        ).status_code
        == 200
    )
    evidence = client.get("/api/v1" + path).json()["events"][0]
    assert evidence["action"] == "Q44" and evidence["facts"]["enrollment_on"] == str(
        day - timedelta(days=1)
    )
    assert evidence["facts"].get("enrollment_at") is None
    assert_balance(db, s["pool"], 0)
