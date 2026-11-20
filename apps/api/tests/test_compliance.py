"""All named persons, appointment instruments and credentials here are isolated test data."""

import base64
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from test_admission import assert_balance
from test_catalog import SOURCE, post
from test_exception_cases import sample, settings  # noqa: F401
from test_outcomes import approve
from test_people import login

from akus.applications.service import today
from akus.compliance.assessment import academic_start, annual_status
from akus.compliance.models import (
    AssessmentSnapshot,
    CredentialDocument,
    CredentialEvent,
    CredentialMandate,
)
from akus.exceptions.models import ArchivedObligation
from akus.models import AcademicYear
from akus.people.models import Person
from akus.sources.models import Subject, TeachingAssignment


def claim(aid, version=0):
    now = datetime.now(UTC)
    pdf = b"%PDF-1.7\nLOCAL_TEST " + str(aid).encode() + b"\n%%EOF"
    return SOURCE | {
        "expected_version": version,
        "observed_at": now.isoformat(),
        "document_digest": hashlib.sha256(pdf).hexdigest(),
        "actual_exam_on": today().isoformat(),
        "sitting": "LOCAL_TEST official sitting",
        "certificate_key": "LOCAL_TEST_" + str(aid),
        "issued_on": today().isoformat(),
        "score_percent": 65,
        "attachment": {
            "base64_data": base64.b64encode(pdf).decode(),
            "media_type": "application/pdf",
        },
    }


def academic_case(client, db):
    day = today()
    s, aid, e, _, _ = sample(client, db, day - timedelta(days=6), True)
    approve(client, aid)
    staff = db.get_one(Person, e.person_id).staff_key
    h = login(client, staff)
    path = f"/certificates/{aid}"
    body = claim(aid)
    key = uuid4()
    r = post(client, path + "/evidence", body, h, key)
    assert r.status_code == 200, r.text
    assert post(client, path + "/evidence", body, h, key).json() == r.json()
    return s, path, e, body, staff


def decision(body):
    return {k: v for k, v in body.items() if k != "attachment"} | {
        "observed_at": datetime.now(UTC).isoformat(),
        "expected_version": 1,
        "actual_exam_at": body["observed_at"],
        "checked_person_offering_certificate": True,
        "verified_exam_and_score_sharing": True,
    }


def appoint(client, db, aid, subject_id=None):
    h = login(client, "acting-hod")
    reviewer = UUID(client.get("/api/v1/me").json()["person_id"])
    db.add(
        CredentialMandate(
            application_id=UUID(aid),
            reviewer_id=reviewer,
            subject_id=subject_id,
            basis="LOCAL_TEST formally documented case designation",
            valid_from=datetime.now(UTC) - timedelta(minutes=1),
            valid_until=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    db.commit()
    return h


def report(client, e, role="principal", snapshot=None):
    login(client, role)
    params = {"scope": "institution" if role == "principal" else "personal"}
    if snapshot:
        params["snapshot_id"] = snapshot
    r = client.get(f"/api/v1/compliance/episodes/{e.id}", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def ay(r):
    return next(y for y in r["annual"] if y["starts_on"] <= str(today()) <= y["ends_on"])


def test_credential_source_lifecycle_and_authority(client, db):
    s, path, e, body, staff = academic_case(client, db)
    aid = path.split("/")[-1]
    decision_body = decision(body)
    initial = report(client, e)
    assert ay(initial)["status"] == "EXAM_REPORTED_PENDING_VERIFICATION"
    snapshot = initial["snapshots"][0]["id"]
    for role in [staff, "hod", "drc", "principal", "admin", "acting-hod"]:
        assert post(client, path + "/verify", decision_body, login(client, role)).status_code == 403
    h = appoint(client, db, aid)
    original = post(client, path + "/verify", decision_body, h)
    assert original.status_code == 200, original.text
    verified = report(client, e)
    y = ay(verified)
    assert y["status"] == "VERIFIED_FULFILLED"
    assert y["allocations"] == [original.json()["id"]]
    assert y["candidates"][0]["score_percent"] == 65
    assert ay(report(client, e, snapshot=snapshot)) == ay(initial)
    h = login(client, "acting-hod")
    assert post(client, path + "/verify", decision_body, h).status_code == 409
    bad = decision_body | {
        "expected_version": 2,
        "observed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    }
    assert post(client, path + "/verify", bad, h).status_code in (409, 422)
    correction = decision_body | {
        "expected_version": 2,
        "score_percent": 82,
        "reason": "LOCAL_TEST official corrected score",
        "observed_at": datetime.now(UTC).isoformat(),
    }
    assert post(client, path + "/verify", correction, h).status_code == 200
    revoke = SOURCE | {
        "expected_version": 3,
        "observed_at": datetime.now(UTC).isoformat(),
        "document_digest": "e" * 64,
        "outcome": "REVOKED",
        "independently_checked": True,
    }
    assert post(client, path + "/disposition", revoke, h).status_code == 200
    assert ay(report(client, e))["allocations"] == []
    assert ay(report(client, e, snapshot=verified["snapshots"][0]["id"])) == y
    assert_balance(db, s["pool"], 1)
    login(client, staff)
    dossier = client.get("/api/v1" + path).json()
    assert [r["kind"] for r in dossier["events"]] == ["REVOKED", "VERIFIED", "VERIFIED", "ASSERTED"]
    doc = dossier["events"][-1]["document_id"]
    assert client.get("/api/v1" + path + "/documents/" + doc).status_code == 423
    login(client, "principal")
    assert client.get("/api/v1" + path + "/documents/" + doc).status_code == 403
    assert db.get_one(CredentialDocument, UUID(doc)).digest == body["document_digest"]


@pytest.mark.parametrize(
    "score,early,accepted,status",
    [
        (75, False, True, "VERIFIED_ON_TIME"),
        (74.99, False, True, "BELOW_SILVER_THRESHOLD"),
        (90, True, True, "EXAM_AFTER_DEADLINE"),
        (90, False, False, "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02"),
    ],
)
def test_active_subject_credit(client, db, score, early, accepted, status):
    s, path, e, body, _ = academic_case(client, db)
    aid = path.split("/")[-1]
    subject = Subject(
        code=uuid4().hex, name="LOCAL_TEST academic subject", source_reference="LOCAL_TEST registry"
    )
    first = today().replace(year=today().year - 2) - timedelta(days=int(early))
    year = db.scalar(select(AcademicYear).where(AcademicYear.starts_on == academic_start(first)))
    if not year:
        start = academic_start(first)
        year = AcademicYear(
            label=f"{start.year}-{start.year + 1}",
            starts_on=start,
            ends_on=date(start.year + 1, 6, 30),
            source="LOCAL_TEST",
        )
        db.add(year)
    db.add(subject)
    db.flush()
    db.add(
        TeachingAssignment(
            external_key=uuid4().hex,
            episode_id=e.id,
            subject_id=subject.id,
            department_id=UUID(s["dept"]),
            academic_year_id=year.id,
            term="LOCAL_TEST",
            starts_on=first,
            ends_before=first + timedelta(days=30),
            source_reference="LOCAL_TEST effective assignment",
        )
    )
    if accepted:
        db.add(
            ArchivedObligation(
                episode_id=e.id,
                subject_id=subject.id,
                first_assignment=first,
                decided_on=first,
                decision_reference="LOCAL_TEST previously adjudicated obligation",
                authority_basis="LOCAL_TEST case ruling",
                document_digest="a" * 64,
            )
        )
    db.commit()
    h = appoint(client, db, aid, subject.id)
    verify = decision(body) | {
        "subject_id": str(subject.id),
        "relevance_basis": "LOCAL_TEST independently assessed official syllabus",
        "score_percent": score,
    }
    assert post(client, path + "/verify", verify, h).status_code == 200
    assessed = report(client, e)
    assert ay(assessed)["status"] == "VERIFIED_FULFILLED"
    row = assessed["silver"][0]
    assert row["status"] == status
    assert (
        row["allocation"] is not None if status == "VERIFIED_ON_TIME" else row["allocation"] is None
    )
    assert row["first_assignment"] == str(first)


def test_parallel_verification_and_capture(client, db):
    from fastapi.testclient import TestClient

    _, path, e, body, staff = academic_case(client, db)
    aid = path.split("/")[-1]
    appoint(client, db, aid)
    packet = decision(body)

    def run(_):
        with TestClient(client.app) as peer:
            return post(peer, path + "/verify", packet, login(peer, "acting-hod")).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == [200, 409]

    def save(_):
        with TestClient(client.app) as peer:
            r = post(peer, "/compliance/snapshots", {"episode_id": str(e.id)}, login(peer, staff))
            assert r.status_code == 200, r.text
            return r.json()["id"]

    with ThreadPoolExecutor(2) as pool:
        assert len(set(pool.map(save, range(2)))) == 1
    assert (
        db.scalar(
            select(func.count())
            .select_from(CredentialEvent)
            .where(CredentialEvent.application_id == UUID(aid), CredentialEvent.kind == "VERIFIED")
        )
        == 1
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(AssessmentSnapshot)
            .where(AssessmentSnapshot.episode_id == e.id)
        )
        == 2
    )


@pytest.mark.parametrize(
    "weeks,courses,expected",
    [
        ([4], ["a"], False),
        ([4, 4], ["a", "b"], True),
        ([4, 4], ["a", "a"], False),
        ([6, 2], ["a", "b"], False),
        ([8], ["a"], True),
    ],
)
def test_annual_paths(weeks, courses, expected):
    rows = [
        {
            "duration_weeks": w,
            "course_id": c,
            "event_id": str(i),
            "eligibility": "ELIGIBLE",
            "status": "VERIFIED",
        }
        for i, (w, c) in enumerate(zip(weeks, courses, strict=True))
    ]
    assert (annual_status(rows)[0] == "VERIFIED_FULFILLED") == expected
    assert academic_start(date(2026, 6, 30)) != academic_start(date(2026, 7, 1))


def test_scope_and_malformed_upload(client, db):
    _, path, e, body, staff = academic_case(client, db)
    assert client.get("/api/v1" + path).status_code == 200
    h = login(client, staff)
    for attachment in [
        {"media_type": "text/html", "base64_data": "PGh0bWw+"},
        {"media_type": "application/pdf", "base64_data": "////////"},
    ]:
        assert (
            post(
                client,
                path + "/evidence",
                body | {"attachment": attachment, "expected_version": 1},
                h,
            ).status_code
            == 422
        )
    assert (
        post(
            client,
            path + "/evidence",
            body | {"document_digest": "0" * 64, "expected_version": 1},
            h,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1" + path + "/evidence", json=body, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 403
    )
    for role in ("admin", "principal", "hod"):
        login(client, role)
        assert client.get("/api/v1/compliance/episodes?scope=personal").status_code == 403
    login(client, "faculty")
    assert client.get(f"/api/v1/compliance/episodes/{e.id}").status_code == 404
    assert client.get("/api/v1" + path).status_code == 404


def test_verified_attendance_does_not_issue_certificate(client, db):
    _, path, e, body, _ = academic_case(client, db)
    h = appoint(client, db, path.split("/")[-1])
    exam = {
        k: body[k]
        for k in ("actual_exam_on", "sitting", "source_reference", "document_digest", "reason")
    }
    exam.update(
        observed_at=datetime.now(UTC).isoformat(),
        expected_version=1,
        checked_person_offering_attendance=True,
    )
    response = post(client, path + "/exam", exam, h)
    assert response.status_code == 200, response.text
    y = ay(report(client, e))
    assert y["status"] == "EXAM_WRITTEN_PENDING_CERTIFICATE" and y["allocations"] == []


def test_certificate_across_june_july_and_late_issue(client, db, monkeypatch):
    from test_admission import draft, observe, setup, submit
    from test_exception_cases import faculty
    from test_participation import proof, verified

    from akus.applications import service as apps
    from akus.exceptions.schemas import IST

    boundary = academic_start(today())
    june = boundary - timedelta(days=1)
    start = june - timedelta(days=60)
    previous_year = academic_start(june)
    if not db.scalar(select(AcademicYear.id).where(AcademicYear.starts_on == previous_year)):
        db.add(
            AcademicYear(
                label=f"{previous_year.year}-{boundary.year}",
                starts_on=previous_year,
                ends_on=june,
                source="LOCAL_TEST",
            )
        )
        db.commit()
    old = datetime.combine(start, datetime.min.time(), IST)

    class SubmitClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return old.astimezone(tz)

    staff = None
    verified_ids = []
    for i, exam in enumerate((june, boundary, june)):
        s = setup(client)
        if not staff:
            staff, ep, _ = faculty(db, s)
        h, offering, patch = observe(
            client,
            s | {"data": s["data"] | {"duration_weeks": 4, "starts_on": str(start)}},
            s["data"]["scheduled_exam_on"],
        )
        assert (
            post(client, f"/admin/nptel/offerings/{offering['id']}/accept", patch, h).status_code
            == 200
        )
        aid, h = draft(client, s, staff)
        with monkeypatch.context() as clock:
            clock.setattr(apps, "datetime", SubmitClock)
            assert submit(client, aid, h).status_code == 200
        enroll = proof(enrolled_at=(old + timedelta(days=1)).isoformat())
        assert post(client, f"/applications/{aid}/enrollment-claims", enroll, h).status_code == 200
        verified(client, aid, enroll)
        approve(client, aid)
        h = login(client, staff)
        c = claim(aid) | {"actual_exam_on": str(exam), "issued_on": str(today())}
        path = "/certificates/" + aid
        assert post(client, path + "/evidence", c, h).status_code == 200
        reviewer = appoint(client, db, aid)
        result = post(client, path + "/verify", decision(c) | {"actual_exam_at": None}, reviewer)
        assert result.status_code == 200, result.text
        verified_ids.append(result.json()["id"])
        report_data = report(client, ep)
        old_year = next(y for y in report_data["annual"] if y["starts_on"] == str(previous_year))
        assert (old_year["status"] == "VERIFIED_FULFILLED") == (i == 2)
        assert ay(report_data)["status"] != "VERIFIED_FULFILLED"
    assert set(old_year["allocations"]) == {verified_ids[0], verified_ids[2]}


def test_distinct_subject_reuse_and_correction_review(client, db):
    from starlette.exceptions import HTTPException

    from akus.applications import outcomes
    from akus.applications import service as apps
    from akus.applications.models import Application
    from akus.compliance.assessment import assess

    s, path, e, body, _ = academic_case(client, db)
    aid = path.split("/")[-1]
    first = today() - timedelta(days=30)
    subjects = [
        Subject(
            code=uuid4().hex, name="LOCAL_TEST " + str(i), source_reference="official test fixture"
        )
        for i in range(2)
    ]
    db.add_all(subjects)
    db.flush()
    assignments = []
    for su in subjects:
        a = TeachingAssignment(
            external_key=uuid4().hex,
            episode_id=e.id,
            subject_id=su.id,
            department_id=UUID(s["dept"]),
            academic_year_id=UUID(s["year"]),
            term="Test",
            starts_on=first,
            ends_before=today(),
            source_reference="LOCAL_TEST",
        )
        db.add(a)
        assignments.append(a)
        db.add(
            ArchivedObligation(
                episode_id=e.id,
                subject_id=su.id,
                first_assignment=first,
                decided_on=first,
                decision_reference="LOCAL_TEST academic decision",
                authority_basis="LOCAL_TEST decision basis",
                document_digest="d" * 64,
            )
        )
    db.commit()
    h = appoint(client, db, aid, subjects[0].id)
    valid = decision(body) | {
        "subject_id": str(subjects[0].id),
        "relevance_basis": "LOCAL_TEST subject relevance",
        "score_percent": 75,
    }
    assert post(client, path + "/verify", valid, h).status_code == 200
    h = appoint(client, db, aid, subjects[1].id)
    assert (
        post(
            client,
            path + "/verify",
            valid | {"expected_version": 2, "subject_id": str(subjects[1].id)},
            h,
        ).status_code
        == 423
    )
    a = db.get_one(Application, UUID(aid))
    prospective = Application(
        id=uuid4(),
        person_id=e.person_id,
        episode_id=uuid4(),
        course_id=a.course_id,
        offering_id=uuid4(),
        state="DRAFT",
    )
    with pytest.raises(HTTPException, match="CANONICAL_COURSE_REPEAT_PROHIBITED_Q28"):
        outcomes.assert_repeat_eligible(db, prospective)
    apps.case(db, a, "INTEGRITY", "LOCAL_TEST_OPEN", {})
    db.commit()
    held = report(client, e)
    assert ay(held)["status"] == "UNDER_INTEGRITY_REVIEW"
    assert all(not r["allocation"] for r in held["silver"])
    assert_balance(db, s["pool"], 1)
    assert len(assess(db, e)["silver"]) == 2


def test_isolated_appointed_browser_fixture(client, db):
    import json

    _, path, e, body, staff = academic_case(client, db)
    aid = path.split("/")[-1]
    appoint(client, db, aid)
    assert client.get("/api/v1" + path).json()["can_verify"] is True
    print(
        "LOCAL_PHASE6_BROWSER="
        + json.dumps(
            {
                "aid": aid,
                "episode": str(e.id),
                "staff": staff,
                "exam_at": body["observed_at"],
                "key": body["certificate_key"],
            }
        )
    )


def test_closed_credential_reassessment_and_frozen_subject(client, db):
    from test_exception_cases import register

    from akus.applications.models import Allocation, Application
    from akus.exceptions.history import report as archived_report
    from akus.exceptions.models import SeparationSnapshot
    from akus.people.models import DepartmentAssignment

    s, path, e, body, _ = academic_case(client, db)
    aid = path.split("/")[-1]
    app = db.get_one(Application, UUID(aid))
    first = today().replace(year=today().year - 2)
    subject = Subject(
        code=uuid4().hex, name="LOCAL_TEST separation subject", source_reference="LOCAL_TEST"
    )
    db.add(subject)
    db.flush()
    db.add(
        TeachingAssignment(
            external_key=uuid4().hex,
            episode_id=e.id,
            subject_id=subject.id,
            department_id=UUID(s["dept"]),
            academic_year_id=UUID(s["year"]),
            term="Local",
            starts_on=first,
            ends_before=first + timedelta(days=1),
            source_reference="LOCAL_TEST",
        )
    )
    db.add(
        ArchivedObligation(
            episode_id=e.id,
            subject_id=subject.id,
            first_assignment=first,
            decided_on=first,
            decision_reference="LOCAL_TEST archived academic ruling",
            authority_basis="LOCAL_TEST separate ruling",
            document_digest="3" * 64,
        )
    )
    db.commit()
    h = appoint(client, db, aid, subject.id)
    valid = decision(body) | {
        "subject_id": str(subject.id),
        "relevance_basis": "LOCALLY adjudicated syllabus match",
        "score_percent": 75,
    }
    assert post(client, path + "/verify", valid, h).status_code == 200
    m = db.scalar(select(DepartmentAssignment).where(DepartmentAssignment.episode_id == e.id))
    cut = datetime.now(UTC)
    oid = register(client, db, e, m, today(), cut)
    original = db.get_one(SeparationSnapshot, oid).subjects[0]
    assert original["status_at_separation"] == "VERIFIED_ON_TIME"
    assert db.get_one(Allocation, UUID(aid)).state == "RELEASED"
    before = datetime.now(UTC)
    assert archived_report(db, app, before)["finding"]["eligibility"] == "ELIGIBLE"
    h = login(client, "acting-hod")
    actual = datetime.now(UTC)
    corrected = valid | {
        "expected_version": 2,
        "actual_exam_at": actual.isoformat(),
        "observed_at": actual.isoformat(),
        "reason": "LOCAL_TEST issuer corrected the sitting",
    }
    result = post(client, path + "/verify", corrected, h)
    assert result.status_code == 200, result.text
    closed = report(client, e)
    row = closed["silver"][0]
    assert (
        row["status_at_separation"] == "VERIFIED_ON_TIME"
        and row["monitoring"] == "CLOSED"
        and row["allocation"] is None
    )
    assert not ay(closed)["allocations"]
    assert archived_report(db, app, before)["finding"]["eligibility"] == "ELIGIBLE"
    assert archived_report(db, app, datetime.now(UTC))["finding"]["eligibility"] != "ELIGIBLE"
    db.expire_all()
    assert db.get_one(Allocation, UUID(aid)).state == "RELEASED"
    assert_balance(db, s["pool"], 0)


def test_report_register_filters_and_historical_cutoff(client, db):
    _, _, e, _, staff = academic_case(client, db)
    params = {
        "scope": "institution",
        "kind": "annual",
        "search": db.get_one(Person, e.person_id).display_name,
    }
    route = "/api/v1/compliance/register"
    login(client, "principal")
    r = client.get(route, params=params | {"limit": 1})
    assert r.status_code == 200, r.text
    page = r.json()
    assert len(page["items"]) == 1 and page["total"] >= 1 and page["years"]
    future = datetime.now(UTC) + timedelta(days=1)
    assert client.get(route, params=params | {"as_of": future.isoformat()}).status_code == 422
    previous = client.get(
        route, params=params | {"as_of": datetime(2000, 1, 1, tzinfo=UTC).isoformat()}
    ).json()
    assert not previous["items"]
    for role in [staff, "admin", "hod"]:
        login(client, role)
        assert client.get(route, params=params).status_code == 403
    assert (
        client.get(route, params=params | {"scope": "department", "kind": "silver"}).status_code
        == 200
    )


def test_document_digest_conflict_and_concurrent_registration(client, db):
    from fastapi.testclient import TestClient

    _, path, _, body, staff = academic_case(client, db)
    _, other, e2, _, other_staff = academic_case(client, db)
    h = login(client, other_staff)
    conflict = post(client, other + "/evidence", body | {"expected_version": 1}, h)
    assert (
        conflict.status_code == 409
        and conflict.json()["error"]["code"] == "DOCUMENT_IDENTITY_CONFLICT"
    )

    def send(_):
        with TestClient(client.app) as peer:
            return post(
                peer,
                path + "/evidence",
                body | {"expected_version": 1, "reason": "LOCAL_TEST amended observation"},
                login(peer, staff),
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(send, range(2))) == [200, 409]
    h = appoint(client, db, path.split("/")[-1])
    assert (
        post(client, path + "/verify", decision(body) | {"expected_version": 2}, h).status_code
        == 200
    )
    h = appoint(client, db, other.split("/")[-1])
    otherbody = decision(claim(other.split("/")[-1])) | {"certificate_key": body["certificate_key"]}
    denied = post(client, other + "/verify", otherbody, h)
    assert (
        denied.status_code == 409
        and denied.json()["error"]["code"] == "CERTIFICATE_IDENTITY_CONFLICT"
    )
    assert not ay(report(client, e2))["allocations"]


def test_corrected_assignment_keeps_adjudicated_deadline_and_source_history(client, db):
    from test_sources import teaching_body

    from akus.compliance.assessment import assess
    from akus.people.models import EmploymentEpisode

    h = login(client, "admin")
    data = teaching_body(client, db, h)
    result = post(client, "/admin/teaching", data, h)
    assert result.status_code == 200, result.text
    ep = db.get_one(EmploymentEpisode, UUID(data["episode_id"]))
    sid = UUID(data["subject_id"])
    first = date.fromisoformat(data["starts_on"])
    db.add(
        ArchivedObligation(
            episode_id=ep.id,
            subject_id=sid,
            first_assignment=first,
            decided_on=first,
            decision_reference="LOCAL_TEST original adjudication",
            authority_basis="LOCAL_TEST signed academic decision",
            document_digest="a" * 64,
        )
    )
    db.commit()
    corrected = post(
        client,
        "/admin/teaching/" + result.json()["id"],
        data | {"expected_version": 1, "starts_on": str(first + timedelta(days=2))},
        h,
    )
    assert corrected.status_code == 200, corrected.text
    row = next(r for r in assess(db, ep)["silver"] if r["subject_id"] == str(sid))
    assert row["first_assignment"] == str(first) and row["revised_source_date"] != str(first)
    assert row["status"] == "ASSIGNMENT_SOURCE_CORRECTION_REVIEW" and not row["allocation"]
    assert (
        db.scalar(
            select(func.count())
            .select_from(AssessmentSnapshot)
            .where(AssessmentSnapshot.episode_id == ep.id)
        )
        >= 2
    )


def test_pending_and_rejected_replacement_preserve_verified_external_result(client, db):
    _, path, e, body, staff = academic_case(client, db)
    h = appoint(client, db, path.split("/")[-1])
    accepted = post(client, path + "/verify", decision(body), h)
    assert accepted.status_code == 200
    h = login(client, staff)
    request = body | {
        "expected_version": 2,
        "observed_at": datetime.now(UTC).isoformat(),
        "score_percent": 92,
        "reason": "LOCAL_TEST unconfirmed revised score",
    }
    assert post(client, path + "/evidence", request, h).status_code == 200
    assert ay(report(client, e))["allocations"] == [accepted.json()["id"]]
    h = login(client, "acting-hod")
    reject = SOURCE | {
        "expected_version": 3,
        "observed_at": datetime.now(UTC).isoformat(),
        "document_digest": "7" * 64,
        "outcome": "REJECTED",
        "independently_checked": True,
    }
    assert post(client, path + "/disposition", reject, h).status_code == 200
    actual = ay(report(client, e))["candidates"][0]
    assert actual["score_percent"] == 65 and actual["event_id"] == accepted.json()["id"]


def test_new_credential_claim_requires_newer_no_certificate_finding(client, db):
    from starlette.exceptions import HTTPException
    from test_outcomes import finding, record

    from akus.applications.models import Application
    from akus.applications.outcomes import assert_repeat_eligible

    s, path, e, body, staff = academic_case(client, db)
    prior = db.get_one(Application, UUID(path.split("/")[-1]))
    attempt = record(client, s, staff, str(prior.offering_id))
    assert finding(client, attempt)[0].status_code == 200
    prospect = Application(
        id=uuid4(),
        person_id=e.person_id,
        course_id=prior.course_id,
        offering_id=uuid4(),
        state="DRAFT",
    )
    assert prior.offering_id in assert_repeat_eligible(db, prospect)
    pending = body | {
        "expected_version": 1,
        "observed_at": datetime.now(UTC).isoformat(),
        "reason": "LOCAL_TEST subsequently reported certificate",
    }
    assert post(client, path + "/evidence", pending, login(client, staff)).status_code == 200
    with pytest.raises(HTTPException, match="PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29"):
        assert_repeat_eligible(db, prospect)
    assert finding(client, attempt)[0].status_code == 200
    assert prior.offering_id in assert_repeat_eligible(db, prospect)
    assert_balance(db, s["pool"], 1)


def test_archived_subject_decision_survives_neutral_credential_revision(client, db):
    from test_exception_cases import register

    from akus.applications.models import Reconciliation
    from akus.exceptions.models import HistoricalMandate
    from akus.people.models import DepartmentAssignment

    s, path, episode, body, _ = academic_case(client, db)
    aid = path.split("/")[-1]
    first = today() - timedelta(days=30)
    subjects = [
        Subject(
            code=uuid4().hex,
            name="LOCAL_TEST historic relevance " + str(i),
            source_reference="LOCAL_TEST",
        )
        for i in range(2)
    ]
    db.add_all(subjects)
    db.flush()
    for subject in subjects:
        db.add(
            TeachingAssignment(
                external_key=uuid4().hex,
                episode_id=episode.id,
                subject_id=subject.id,
                department_id=UUID(s["dept"]),
                academic_year_id=UUID(s["year"]),
                term="Local",
                starts_on=first,
                ends_before=today(),
                source_reference="LOCAL_TEST",
            )
        )
        db.add(
            ArchivedObligation(
                episode_id=episode.id,
                subject_id=subject.id,
                first_assignment=first,
                decided_on=first,
                decision_reference="LOCAL_TEST archived adjudication",
                authority_basis="LOCAL_TEST subject decision",
                document_digest="a" * 64,
            )
        )
    db.commit()
    h = appoint(client, db, aid)
    neutral = decision(body) | {"score_percent": 80}
    accepted = post(client, path + "/verify", neutral, h)
    assert accepted.status_code == 200
    member = db.scalar(
        select(DepartmentAssignment).where(DepartmentAssignment.episode_id == episode.id)
    )
    register(client, db, episode, member, today(), datetime.now(UTC))
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.kind == "SEPARATION", Reconciliation.application_id == UUID(aid)
        )
    )
    h = login(client, "acting-hod")
    reviewer = UUID(client.get("/api/v1/me").json()["person_id"])
    now = datetime.now(UTC)
    db.add(
        HistoricalMandate(
            case_id=case.id,
            reviewer_id=reviewer,
            subject_id=subjects[0].id,
            basis="LOCAL_TEST archived relevance order",
            valid_from=now - timedelta(minutes=1),
            valid_until=now + timedelta(hours=1),
        )
    )
    db.commit()
    evidence = SOURCE | {
        "finding_id": accepted.json()["id"],
        "subject_id": str(subjects[0].id),
        "checked_subject_relevance": True,
        "relevance_basis": "LOCAL_TEST formally accepted syllabus",
        "observed_at": now.isoformat(),
        "document_digest": "f" * 64,
    }
    result = post(client, f"/separation-cases/{case.id}/historical-review/subject", evidence, h)
    assert result.status_code == 200, result.text
    old = report(client, episode)
    assert (
        next(r for r in old["silver"] if r["subject_id"] == str(subjects[0].id))["allocation"]
        == accepted.json()["id"]
    )
    h = login(client, "acting-hod")
    revision = neutral | {
        "expected_version": 2,
        "score_percent": 82,
        "observed_at": datetime.now(UTC).isoformat(),
    }
    assert post(client, path + "/verify", revision, h).status_code == 200
    corrected_row = next(
        r for r in report(client, episode)["silver"] if r["subject_id"] == str(subjects[0].id)
    )
    assert (
        corrected_row["status"] == "VERIFIED_ON_TIME"
        and corrected_row["candidates"][0]["score_percent"] == 82
    )
    h = appoint(client, db, aid, subjects[1].id)
    denied = post(
        client,
        path + "/verify",
        revision
        | {
            "expected_version": 3,
            "subject_id": str(subjects[1].id),
            "relevance_basis": "LOCAL_TEST second claimed subject",
        },
        h,
    )
    assert (
        denied.status_code == 423
        and denied.json()["error"]["code"] == "MULTIPLE_SUBJECT_USE_POLICY_PENDING_Q51"
    )
    assert_balance(db, s["pool"], 0)


def test_historical_report_respects_invalidation_at_knowledge_cutoff(client, db):
    from test_exception_cases import decision as case_decision
    from test_exception_cases import dossier

    from akus.applications import service
    from akus.applications.models import Application
    from akus.exceptions.history import report as historical
    from akus.exceptions.models import IntegrityMandate

    s, path, episode, body, _ = academic_case(client, db)
    aid = path.split("/")[-1]
    h = appoint(client, db, aid)
    assert post(client, path + "/verify", decision(body), h).status_code == 200
    app = db.get_one(Application, UUID(aid))
    before = datetime.now(UTC)
    assert historical(db, app, before)["finding"]["eligibility"] == "ELIGIBLE"
    service.case(
        db,
        app,
        "INTEGRITY",
        "PRIOR_CERTIFICATE_AUTHORITY_POLICY_PENDING",
        {"recognition": "SUSPENDED"},
    )
    db.commit()
    route, case, _ = dossier(client, db, aid, kind="INTEGRITY")
    during = datetime.now(UTC)
    assert historical(db, app, during)["finding"]["eligibility"] == "SUSPENDED_PENDING_REVIEW"
    h = login(client, "faculty")
    pid = UUID(client.get("/api/v1/me").json()["person_id"])
    db.add(
        IntegrityMandate(
            case_id=UUID(case["id"]),
            reviewer_id=pid,
            basis="LOCAL_TEST case-specific independent designation",
            valid_from=before,
            valid_until=before + timedelta(hours=1),
        )
    )
    db.commit()
    result = post(client, route + "/decision", case_decision(case, "INVALIDATE"), h)
    assert result.status_code == 200, result.text
    after = historical(db, app, datetime.now(UTC))
    assert after["finding"]["eligibility"] == "APPROVAL_INVALIDATED" and not after["annual"]
    assert historical(db, app, before)["finding"]["eligibility"] == "ELIGIBLE"
    assert historical(db, app, during)["finding"]["eligibility"] == "SUSPENDED_PENDING_REVIEW"
    assert not ay(report(client, episode))["allocations"]
    assert_balance(db, s["pool"], 0)
