"""Source-record vertical slice: real PostgreSQL, actual API/session permissions."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from akus.access import authority
from akus.models import AuthSession, DemoIdentity
from akus.people.models import (
    AdministrativeGrant,
    CommandReceipt,
    Department,
    EmploymentEpisode,
    OfficeAppointment,
    Person,
)
from akus.people.seed import fixture_id

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def login(client, key="admin"):
    r = client.post("/api/v1/auth/demo-login", json={"identity_key": key}, headers=ORIGIN)
    assert r.status_code == 200, r.text
    return ORIGIN | {"X-CSRF-Token": r.json()["csrf_token"], "Idempotency-Key": str(uuid4())}


def staff_body(dept=None, faculty=True):
    return dict(
        staff_key=f"TEST-{uuid4().hex[:16].upper()}",
        display_name="Local test person",
        department_id=str(dept or fixture_id("CSE")),
        starts_on="2020-07-01",
        is_faculty=faculty,
        source_reference="LOCAL_TEST_ORDER",
        reason="Isolated test source",
    )


def create_person(client, headers, dept=None, faculty=True):
    r = client.post(
        "/api/v1/admin/staff",
        headers=headers | {"Idempotency-Key": str(uuid4())},
        json=staff_body(dept, faculty),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def fresh_dept(db):
    row = Department(code=f"T{uuid4().hex[:12]}", name="Local test department")
    db.add(row)
    db.commit()
    return row.id


def office_body(person, dept, office="DRC_HEAD", start=None, end=None):
    return dict(
        person_id=str(person),
        department_id=str(dept) if dept else None,
        office=office,
        valid_from=(start or datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        valid_until=end.isoformat() if end else None,
        source_reference="LOCAL_TEST_APPOINTMENT",
        reason="Isolated appointment test",
    )


def appoint(client, headers, body):
    return client.post(
        "/api/v1/admin/appointments", headers=headers | {"Idempotency-Key": str(uuid4())}, json=body
    )


@pytest.mark.parametrize(
    "key,eligible,directory",
    [
        ("faculty", True, False),
        ("drc", True, False),
        ("hod", False, True),
        ("acting-hod", False, True),
        ("principal", False, True),
        ("admin", False, True),
    ],
)
def test_current_roles_and_filtered_reads(client, key, eligible, directory):
    login(client, key)
    me = client.get("/api/v1/me").json()
    assert me["applicant_eligible"] is eligible
    assert me["can_read_directory"] is directory
    assert client.get("/api/v1/me/authority").status_code == 200
    result = client.get("/api/v1/people/staff?limit=100")
    assert result.status_code == (200 if directory else 403)
    if key in ("hod", "acting-hod"):
        assert {r["department_id"] for r in result.json()["items"]} <= set(me["department_ids"])
        assert (
            client.get(f"/api/v1/people/staff/{fixture_id('person/principal')}").status_code == 404
        )
        offices = client.get("/api/v1/people/appointments?limit=100").json()["items"]
        assert {r["department_id"] for r in offices} <= set(me["department_ids"])
    if not directory:
        assert client.get(f"/api/v1/people/staff/{fixture_id('person/admin')}").status_code == 404


@pytest.mark.parametrize("key", ["faculty", "drc", "hod", "acting-hod", "principal"])
def test_non_admin_cannot_write_even_with_csrf(client, key):
    headers = login(client, key)
    assert client.post("/api/v1/admin/staff", headers=headers, json=staff_body()).status_code == 403
    assert (
        appoint(client, headers, office_body(fixture_id("faculty"), fixture_id("OPS"))).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/admin/appointments/{uuid4()}/end",
            headers=headers,
            json={"expected_version": 1, "reason": "Attempt unauthorized end"},
        ).status_code
        == 403
    )


def test_staff_command_atomic_idempotent_and_csrf(client, db):
    headers = login(client)
    body = staff_body()
    assert client.post("/api/v1/admin/staff", json=body, headers=ORIGIN).status_code == 422
    assert (
        client.post(
            "/api/v1/admin/staff", json=body, headers=headers | {"X-CSRF-Token": "wrong"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/admin/staff", json=body, headers=headers | {"Origin": "https://evil.invalid"}
        ).status_code
        == 403
    )
    assert db.scalar(select(Person).where(Person.staff_key == body["staff_key"])) is None
    response = client.post("/api/v1/admin/staff", json=body, headers=headers)
    assert response.status_code == 201, response.text
    assert client.post("/api/v1/admin/staff", json=body, headers=headers).json() == response.json()
    assert (
        client.post(
            "/api/v1/admin/staff", json=body | {"display_name": "Different"}, headers=headers
        ).status_code
        == 409
    )
    person = UUID(response.json()["id"])
    detail = client.get(f"/api/v1/people/staff/{person}").json()
    assert len(detail["episodes"]) == 1
    assert len(detail["events"]) == 1
    assert detail["events"][0]["details"]["reason"] == body["reason"]
    assert db.get(Person, person).demo_identity_id is None
    assert (
        db.scalar(
            select(func.count())
            .select_from(CommandReceipt)
            .where(CommandReceipt.key == UUID(headers["Idempotency-Key"]))
        )
        == 1
    )
    assert (
        client.post(
            "/api/v1/admin/staff", json=body, headers=headers | {"Idempotency-Key": str(uuid4())}
        ).status_code
        == 409
    )
    assert client.get("/api/v1/people/staff?q=%25").json()["total"] == 0  # literal %, not wildcard
    assert client.get("/api/v1/people/staff?limit=101").status_code == 422


def test_global_cross_department_exclusion_and_pending_principal(client, db):
    headers = login(client)
    person = create_person(client, headers)
    d1, d2 = fresh_dept(db), fresh_dept(db)
    assert appoint(client, headers, office_body(person, d1)).status_code == 201
    for role in ["HOD", "ACTING_HOD"]:
        response = appoint(client, headers, office_body(person, d2, role))
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "OFFICE_INTERVAL_CONFLICT"
    pending = appoint(client, headers, office_body(person, None, "PRINCIPAL"))
    assert pending.status_code == 423
    assert pending.json()["error"]["code"] == "AUTHORITY_POLICY_PENDING"
    assert len(client.get(f"/api/v1/people/staff/{person}").json()["appointments"]) == 1


def test_office_boundaries_and_same_role_different_scope(client, db):
    headers = login(client)
    person = create_person(client, headers)
    d1, d2 = fresh_dept(db), fresh_dept(db)
    start = datetime(2040, 1, 1, tzinfo=UTC)
    boundary = start + timedelta(days=2)
    assert (
        appoint(client, headers, office_body(person, d1, "DRC_HEAD", start, boundary)).status_code
        == 201
    )
    assert appoint(client, headers, office_body(person, d2, "HOD", boundary)).status_code == 201
    # I02 does not prohibit the SAME office across scopes; do not invent that policy.
    assert appoint(client, headers, office_body(person, d1, "HOD", boundary)).status_code == 201
    invalid = office_body(person, d2, "HOD", boundary, boundary)
    assert appoint(client, headers, invalid).status_code == 422
    invalid["valid_from"] = "2040-01-01T00:00:00"  # no zone
    assert appoint(client, headers, invalid).status_code == 422


def test_drc_requires_faculty_and_office_requires_employment(client, db):
    headers = login(client)
    person = create_person(client, headers, faculty=False)
    assert appoint(client, headers, office_body(person, fresh_dept(db))).status_code == 422
    person = create_person(client, headers)
    result = appoint(
        client, headers, office_body(person, fresh_dept(db), start=datetime(2010, 1, 1, tzinfo=UTC))
    )
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "OFFICE_OUTSIDE_EMPLOYMENT"


def test_end_is_versioned_idempotent_and_preserves_issued_record(client, db):
    headers = login(client)
    person = create_person(client, headers)
    body = office_body(person, fresh_dept(db), end=datetime.now(UTC) + timedelta(days=2))
    appointment = appoint(client, headers, body).json()["id"]
    end = {"expected_version": 1, "reason": "Formal local appointment end"}
    headers = headers | {"Idempotency-Key": str(uuid4())}
    url = f"/api/v1/admin/appointments/{appointment}/end"
    assert client.post(url, json=end | {"expected_version": 2}, headers=headers).status_code == 409
    assert client.post(url, json=end, headers=headers).status_code == 200
    assert client.post(url, json=end, headers=headers).status_code == 200
    assert (
        client.post(url, json=end, headers=headers | {"Idempotency-Key": str(uuid4())}).status_code
        == 409
    )
    record = db.get(OfficeAppointment, UUID(appointment))
    assert record.version == 2 and record.valid_until < record.original_until
    detail = client.get(f"/api/v1/people/staff/{person}").json()
    assert sum(e["action"] == "OFFICE_ENDED" for e in detail["events"]) == 1
    assert detail["appointments"][0]["status"] == "ENDED"
    for sql in [
        "UPDATE office_appointments SET reason='forged' WHERE id=:id",
        "UPDATE office_appointments SET valid_until=NULL, version=3 WHERE id=:id",
        "DELETE FROM office_appointments WHERE id=:id",
    ]:
        with pytest.raises(DBAPIError):
            db.execute(text(sql), {"id": appointment})
            db.commit()
        db.rollback()


def test_appointment_changes_live_session_authority_and_end_revokes(client, db):
    admin_headers = login(client)
    # Separate clients share app/factory, not cookies. No new identity/provider fixture.
    with TestClient(client.app) as faculty:
        login(faculty, "faculty")
        person = faculty.get("/api/v1/me").json()["person_id"]
        dept = fresh_dept(db)
        body = office_body(person, dept, "HOD")
        appointment = appoint(client, admin_headers, body).json()["id"]
        try:
            me = faculty.get("/api/v1/me").json()
            assert me["role"] == "HOD" and not me["applicant_eligible"]
            assert (
                faculty.get("/api/v1/me/authority").status_code == 200
            )  # own home differs from office
            assert faculty.get("/api/v1/people/staff").status_code == 200
        finally:
            result = client.post(
                f"/api/v1/admin/appointments/{appointment}/end",
                headers=admin_headers,
                json={"expected_version": 1, "reason": "End temporary test appointment"},
            )
            assert result.status_code == 200, result.text
        assert faculty.get("/api/v1/me").json()["role"] == "FACULTY"
        assert faculty.get("/api/v1/people/staff").status_code == 403


def test_demo_role_label_cannot_elevate_and_disabled_staff_session_revoked(client, db):
    demo = db.scalar(select(DemoIdentity).where(DemoIdentity.key == "faculty"))
    person = db.get(Person, fixture_id("faculty"))
    demo.role = "ADMIN"
    db.commit()
    try:
        login(client, "faculty")
        assert client.get("/api/v1/me").json()["role"] == "FACULTY"
        person.enabled = False
        db.commit()
        assert client.get("/api/v1/me").status_code == 403
        assert client.get("/api/v1/me").status_code == 401
    finally:
        person.enabled = True
        demo.role = "FACULTY"
        db.commit()


def test_scheduled_and_expired_offices_grant_nothing(client, db):
    login(client, "faculty")
    now = datetime.now(UTC)
    person = fixture_id("faculty")
    dept = fresh_dept(db)
    for start, end in [
        (now - timedelta(days=3), now - timedelta(days=2)),
        (now + timedelta(days=3), now + timedelta(days=4)),
    ]:
        db.add(
            OfficeAppointment(
                person_id=person,
                department_id=dept,
                office="HOD",
                valid_from=start,
                valid_until=end,
                original_until=end,
                source_reference="LOCAL_TEST",
                reason="Temporal resolution",
            )
        )
    db.commit()
    assert client.get("/api/v1/me").json()["role"] == "FACULTY"
    demo = db.scalar(select(DemoIdentity).where(DemoIdentity.key == "faculty"))
    session = db.scalar(select(AuthSession).where(AuthSession.identity_id == demo.id))
    assert authority(db, demo, session, now + timedelta(days=3)).primary_role == "HOD"
    assert authority(db, demo, session, now + timedelta(days=4)).primary_role == "FACULTY"


def test_rehire_keeps_identity_and_episodes_do_not_overlap(client, db):
    login(client)
    person = fixture_id("rehired")
    history = client.get(f"/api/v1/people/staff/{person}").json()
    assert len(history["episodes"]) == 2
    db.add(
        EmploymentEpisode(
            person_id=person,
            starts_on=date(2021, 1, 1),
            ends_before=date(2022, 1, 1),
            is_faculty=True,
            source_reference="LOCAL_TEST",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_global_exclusion_with_two_concurrent_database_writers(client, db):
    headers = login(client)
    person = UUID(create_person(client, headers))
    depts = [fresh_dept(db), fresh_dept(db)]
    barrier = Barrier(2)
    factory = client.app.state.sessions
    start = datetime(2050, 1, 1, tzinfo=UTC)

    def run(i):
        with factory() as session:
            session.add(
                OfficeAppointment(
                    person_id=person,
                    department_id=depts[i],
                    office=["DRC_HEAD", "ACTING_HOD"][i],
                    valid_from=start,
                    valid_until=None,
                    original_until=None,
                    source_reference="LOCAL_RACE",
                    reason="Concurrent conflicting appointments",
                )
            )
            barrier.wait(timeout=10)
            try:
                session.commit()
                return "committed"
            except IntegrityError as exc:
                assert exc.orig.sqlstate == "23P01"  # exclusion_violation
                session.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, range(2))) == ["committed", "conflict"]
    assert (
        db.scalar(
            select(func.count())
            .select_from(OfficeAppointment)
            .where(OfficeAppointment.person_id == person)
        )
        == 1
    )


def test_authority_rechecked_before_idempotent_replay(client, db):
    headers = login(client)
    body = staff_body()
    assert client.post("/api/v1/admin/staff", headers=headers, json=body).status_code == 201
    grant = db.scalar(
        select(AdministrativeGrant).where(AdministrativeGrant.person_id == fixture_id("admin"))
    )
    old = grant.valid_until
    grant.valid_until = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    try:
        assert client.post("/api/v1/admin/staff", headers=headers, json=body).status_code == 403
    finally:
        grant.valid_until = old
        db.commit()


def test_appointment_record_reads_require_own_or_scoped_authority(client):
    login(client, "faculty")
    drc_office = fixture_id("office/drc")
    assert client.get(f"/api/v1/people/appointments/{drc_office}").status_code == 404
    login(client, "drc")
    assert client.get(f"/api/v1/people/appointments/{drc_office}").status_code == 200
    login(client, "acting-hod")
    assert client.get(f"/api/v1/people/appointments/{drc_office}").status_code == 404
    login(client, "principal")
    assert client.get(f"/api/v1/people/appointments/{drc_office}").status_code == 200


def test_duplicate_concurrent_source_command_commits_once(client, db):
    headers = login(client)
    body = staff_body()
    barrier = Barrier(2)

    def run(_):
        with TestClient(client.app) as other:
            other.cookies.update(client.cookies)
            barrier.wait(timeout=10)
            r = other.post("/api/v1/admin/staff", headers=headers, json=body)
            assert r.status_code == 201, r.text
            return r.json()["id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(run, range(2)))
    assert ids[0] == ids[1]
    assert (
        db.scalar(
            select(func.count())
            .select_from(CommandReceipt)
            .where(CommandReceipt.key == UUID(headers["Idempotency-Key"]))
        )
        == 1
    )
