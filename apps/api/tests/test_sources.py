from concurrent.futures import ThreadPoolExecutor
from datetime import date
from io import BytesIO
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from openpyxl import Workbook
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_people import appoint, create_person, fresh_dept, login, office_body

from akus.access import authority
from akus.auth import digest
from akus.models import AcademicYear, AuthSession, DemoIdentity
from akus.people.models import EmploymentEpisode, OfficeAppointment, Person
from akus.people.seed import fixture_id
from akus.sources import imports
from akus.sources.models import SourceRevision, TeachingAssignment


def post(client, path, body, headers):
    return client.post(path, json=body, headers=headers | {"Idempotency-Key": str(uuid4())})


def subject(client, headers):
    result = post(
        client,
        "/api/v1/admin/reference",
        {
            "kind": "subject",
            "code": f"T{uuid4().hex[:12].upper()}",
            "name": "Synthetic source subject",
            "source_reference": "LOCAL_TEST_ONLY",
            "reason": "Official synthetic test source",
        },
        headers,
    )
    assert result.status_code == 200, result.text
    return result.json()["id"]


def teaching_body(client, db, headers, person_id=None):
    person_id = person_id or create_person(client, headers)
    episode = db.scalar(
        select(EmploymentEpisode).where(EmploymentEpisode.person_id == UUID(person_id))
    )
    year = db.scalar(select(AcademicYear).where(AcademicYear.starts_on == date(2026, 7, 1)))
    return {
        "external_key": f"TEST-{uuid4().hex}",
        "episode_id": str(episode.id),
        "subject_id": subject(client, headers),
        "department_id": str(fixture_id("CSE")),
        "academic_year_id": str(year.id),
        "term": "Synthetic semester 1",
        "starts_on": "2026-07-10",
        "ends_before": "2026-11-01",
        "source_reference": "LOCAL_TEST_ONLY",
        "reason": "Synthetic official teaching source",
    }


def test_teaching_clock_continuity_correction_void_and_audit(client, db):
    headers = login(client)
    body = teaching_body(client, db, headers)
    first = post(client, "/api/v1/admin/teaching", body, headers)
    assert first.status_code == 200, first.text
    first_id = first.json()["id"]
    second = post(
        client,
        "/api/v1/admin/teaching",
        body
        | {
            "external_key": f"TEST-{uuid4().hex}",
            "starts_on": "2027-01-01",
            "ends_before": "2027-04-01",
        },
        headers,
    )
    assert second.status_code == 200, second.text
    second_id = second.json()["id"]
    view = client.get(f"/api/v1/teaching/{second_id}").json()
    assert view["first_official_date"] == "2026-07-10"
    assert view["provisional_deadline"] == "2028-07-10"
    assert view["acceptance"] == "POLICY_PENDING:IO-02" and view["compliance"] == "NOT_ASSESSED"
    correction = body | {
        "starts_on": "2026-07-20",
        "expected_version": 1,
        "reason": "Correct official start-date typo",
    }
    assert (
        post(client, f"/api/v1/admin/teaching/{first_id}", correction, headers).status_code == 200
    )
    assert (
        post(client, f"/api/v1/admin/teaching/{first_id}", correction, headers).status_code == 409
    )
    view = client.get(f"/api/v1/teaching/{first_id}").json()
    assert view["first_official_date"] == "2026-07-20"
    assert view["history"][0]["before"]["starts_on"] == "2026-07-10"
    assert (
        post(
            client,
            f"/api/v1/admin/teaching/{first_id}",
            correction | {"expected_version": 2, "voided": True},
            headers,
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/teaching/{second_id}").json()["first_official_date"] == "2027-01-01"


def test_teaching_overlap_and_outside_dates_rejected(client, db):
    headers = login(client)
    body = teaching_body(client, db, headers)
    assert post(client, "/api/v1/admin/teaching", body, headers).status_code == 200
    assert (
        post(
            client,
            "/api/v1/admin/teaching",
            body | {"external_key": f"TEST-{uuid4().hex}"},
            headers,
        ).status_code
        == 409
    )
    assert (
        post(
            client, "/api/v1/admin/teaching", body | {"starts_on": "2025-01-01"}, headers
        ).status_code
        == 422
    )


@pytest.mark.parametrize("role", ["faculty", "drc", "hod", "principal"])
def test_teaching_reference_import_write_denied_by_role(client, db, role):
    headers = login(client)
    body = teaching_body(client, db, headers)
    created = post(client, "/api/v1/admin/teaching", body, headers).json()["id"]
    headers = login(client, role)
    assert post(client, "/api/v1/admin/teaching", body, headers).status_code == 403
    assert (
        post(
            client,
            "/api/v1/admin/reference",
            {
                "kind": "subject",
                "code": "T",
                "name": "Synthetic",
                "source_reference": "TEST",
                "reason": "Forbidden role",
            },
            headers,
        ).status_code
        == 403
    )
    assert client.get("/api/v1/admin/imports").status_code == 403
    assert client.get(f"/api/v1/teaching/{created}").status_code == (
        200 if role in {"hod", "principal"} else 404
    )


def upload(client, headers, kind, content, filename="roster.csv", source=None):
    return client.post(
        "/api/v1/admin/imports",
        headers={k: v for k, v in headers.items() if k != "Idempotency-Key"},
        data={"kind": kind, "source_reference": source or f"LOCAL_TEST_{uuid4().hex}"},
        files={"file": (filename, content)},
    )


def staff_csv(key=None, email=""):
    return (
        "staff_key,display_name,department_code,starts_on,ends_before,is_faculty,email,email_valid_from\n"
        f"{key or 'IMPORT-' + uuid4().hex[:12].upper()},Synthetic imported staff,CSE,2020-07-01,,true,{email},{'2020-07-01T00:00:00Z' if email else ''}\n"
    ).encode()


def test_staff_csv_staging_commit_retry_and_source_history(client, db):
    headers = login(client)
    key = f"IMPORT-{uuid4().hex[:12].upper()}"
    content = staff_csv(key, f"{uuid4().hex}@example.test")
    source = f"LOCAL_TEST_{uuid4().hex}"
    staged = upload(client, headers, "staff", content, source=source)
    assert staged.status_code == 201, staged.text
    record = staged.json()
    assert record["error_count"] == 0
    assert db.scalar(select(Person.id).where(Person.staff_key == key)) is None
    assert upload(client, headers, "staff", content, source=source).json()["id"] == record["id"]
    for _ in range(2):
        committed = post(
            client,
            f"/api/v1/admin/imports/{record['id']}/commit",
            {"confirm_authoritative_source": True},
            headers,
        )
        assert committed.status_code == 200 and committed.json()["status"] == "COMMITTED"
    person = db.scalar(select(Person).where(Person.staff_key == key))
    assert person.demo_identity_id is None
    assert db.scalar(select(func.count()).select_from(Person).where(Person.staff_key == key)) == 1
    history = db.scalar(select(SourceRevision).where(SourceRevision.entity_id == person.id))
    assert record["id"] in history.context["reason"]


def test_teaching_xlsx_import_is_pending_and_correctable(client, db):
    headers = login(client)
    body = teaching_body(client, db, headers)
    episode = db.get(EmploymentEpisode, UUID(body["episode_id"]))
    person = db.get(Person, episode.person_id)
    from akus.sources.models import Subject

    sub = db.get(Subject, UUID(body["subject_id"]))
    workbook = Workbook()
    workbook.active.append(
        [
            "external_key",
            "staff_key",
            "episode_starts_on",
            "subject_code",
            "department_code",
            "academic_year_start",
            "term",
            "starts_on",
            "ends_before",
        ]
    )
    workbook.active.append(
        [
            body["external_key"],
            person.staff_key,
            "2020-07-01",
            sub.code,
            "CSE",
            "2026-07-01",
            "Synthetic term",
            "2026-07-10",
            "2026-11-01",
        ]
    )
    stream = BytesIO()
    workbook.save(stream)
    result = upload(client, headers, "teaching", stream.getvalue(), filename="teaching.xlsx")
    assert result.status_code == 201 and result.json()["error_count"] == 0, result.text
    record_id = result.json()["id"]
    assert (
        post(
            client,
            f"/api/v1/admin/imports/{record_id}/commit",
            {"confirm_authoritative_source": True},
            headers,
        ).status_code
        == 200
    )
    record = db.scalar(
        select(TeachingAssignment).where(TeachingAssignment.external_key == body["external_key"])
    )
    assert (
        client.get(f"/api/v1/teaching/{record.id}").json()["acceptance"] == "POLICY_PENDING:IO-02"
    )


def test_invalid_import_rows_persist_and_commit_is_all_or_nothing(client, db):
    headers = login(client)
    key = f"IMPORT-{uuid4().hex[:12].upper()}"
    content = staff_csv(key) + b"BAD,Invalid row,UNKNOWN,not-a-date,,true,,\n"
    result = upload(client, headers, "staff", content).json()
    assert result["error_count"] == 1
    assert (
        post(
            client,
            f"/api/v1/admin/imports/{result['id']}/commit",
            {"confirm_authoritative_source": True},
            headers,
        ).status_code
        == 409
    )
    assert (
        client.get(f"/api/v1/admin/imports/{result['id']}").json()["status"] == "VALIDATION_FAILED"
    )
    assert db.scalar(select(Person.id).where(Person.staff_key == key)) is None


def test_duplicate_rows_and_real_roster_in_demo_rejected(client):
    headers = login(client)
    content = staff_csv("IMPORT-DUPLICATE")
    result = upload(client, headers, "staff", content + content.split(b"\n")[1] + b"\n").json()
    assert result["error_count"] >= 1
    result = upload(client, headers, "staff", staff_csv(email="synthetic@cmrit.ac.in")).json()
    assert result["rows"][0]["errors"] == ["EMAIL_ENVIRONMENT_BOUNDARY"]


@pytest.mark.parametrize(
    "filename,content,status",
    [
        ("malware.exe", b"binary", 415),
        ("large.csv", b"a" * (4 * 1024 * 1024 + 1), 413),
        ("bad.xlsx", b"not a zip", 422),
        ("formula.csv", b"staff_key,display_name\nA,=HYPERLINK(attack)\n", 422),
    ],
)
def test_import_file_boundaries(client, filename, content, status):
    assert upload(client, login(client), "staff", content, filename=filename).status_code == status


def test_source_correction_preserves_facts_and_requires_current_version(client, db):
    headers = login(client)
    person = create_person(client, headers)
    original = client.get(f"/api/v1/people/staff/{person}/sources").json()
    body = {
        "kind": "person",
        "expected_version": original["person"]["source_version"],
        "values": {"display_name": "Corrected synthetic name", "enabled": True},
        "source_reference": "LOCAL_CORRECTION_ORDER",
        "reason": "Official source name correction",
    }
    assert post(client, f"/api/v1/admin/staff/{person}/sources", body, headers).status_code == 200
    assert post(client, f"/api/v1/admin/staff/{person}/sources", body, headers).status_code == 409
    result = client.get(f"/api/v1/people/staff/{person}/sources").json()
    change = next(r for r in result["history"] if r["entity_type"] == "persons" and r["before"])
    assert change["before"]["display_name"] == "Local test person"
    assert change["after"]["display_name"] == "Corrected synthetic name"
    for sql in [
        "UPDATE source_revisions SET context='{}' WHERE id=:id",
        "DELETE FROM source_revisions WHERE id=:id",
    ]:
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(text(sql), {"id": UUID(change["id"])})


def test_office_correction_preserves_original_and_rechecks_global_exclusion(client, db):
    headers = login(client)
    person = create_person(client, headers)
    department = fresh_dept(db)
    original = office_body(person, department)
    record_id = appoint(client, headers, original).json()["id"]
    body = {
        "kind": "office",
        "id": record_id,
        "expected_version": 1,
        "values": {
            "office": "HOD",
            "department_id": str(department),
            "valid_from": original["valid_from"],
            "valid_until": None,
        },
        "source_reference": "LOCAL_CORRECTION_ORDER",
        "reason": "Official mistaken-office correction",
    }
    changed = post(client, f"/api/v1/admin/staff/{person}/sources", body, headers)
    assert changed.status_code == 200, changed.text
    db.expire_all()
    old = db.get(OfficeAppointment, UUID(record_id))
    assert old.superseded and old.office == "DRC_HEAD"
    assert db.get(OfficeAppointment, UUID(changed.json()["id"])).office == "HOD"
    conflict = office_body(person, fresh_dept(db), "DRC_HEAD")
    assert appoint(client, headers, conflict).status_code == 409


def test_dashboard_and_academic_integration_role_boundaries(client):
    for key, role, route in [
        ("faculty", "FACULTY", ["DRC_HEAD", "HOD"]),
        ("drc", "DRC_HEAD", ["HOD"]),
        ("hod", "HOD", []),
        ("principal", "PRINCIPAL", []),
        ("admin", "ADMIN", []),
    ]:
        login(client, key)
        dash = client.get("/api/v1/dashboard").json()
        assert dash["role"] == role and dash["own_review_route"] == route
        assert dash["academic_status"] == "CATALOG_ADMISSION_AVAILABLE"
        assert client.get("/api/v1/academic/integration/applications").status_code == (
            200 if route else 403
        )
        reviews = client.get("/api/v1/academic/integration/reviews")
        assert reviews.status_code == (200 if role in {"DRC_HEAD", "HOD"} else 403)
        if reviews.status_code == 200:
            assert reviews.json()["status"] == "AVAILABLE"
            assert reviews.json()["can_decide"] is False and reviews.json()["records"] is None
        if role == "PRINCIPAL":
            assert len(dash["departments"]) >= 3


def test_same_import_commits_once_under_race(client, db, settings):
    headers = login(client)
    key = f"RACE-{uuid4().hex[:12].upper()}"
    job = upload(client, headers, "staff", staff_csv(key)).json()
    identity = db.scalar(select(DemoIdentity).where(DemoIdentity.key == "admin"))
    auth_session = db.get(AuthSession, digest(client.cookies.get("akus_demo_session")))
    session_hash = auth_session.token_hash
    barrier = Barrier(6)

    def contender(_):
        with client.app.state.sessions() as connection:
            demo = connection.get(DemoIdentity, identity.id)
            actor = authority(connection, demo, connection.get(AuthSession, session_hash))
            barrier.wait(timeout=10)
            return imports.commit(connection, actor, UUID(job["id"]), settings).status

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert list(pool.map(contender, range(6))) == ["COMMITTED"] * 6
    assert db.scalar(select(func.count()).select_from(Person).where(Person.staff_key == key)) == 1


def test_session_revoked_after_authority_read_cannot_execute_source_command(client, db):
    from starlette.exceptions import HTTPException
    from test_people import staff_body

    from akus.people.schemas import StaffCreate
    from akus.people.service import create_staff

    login(client)
    identity = db.scalar(select(DemoIdentity).where(DemoIdentity.key == "admin"))
    auth_session = db.get(AuthSession, digest(client.cookies.get("akus_demo_session")))
    actor = authority(db, identity, auth_session)
    with client.app.state.sessions() as other:
        revoked = other.get(AuthSession, auth_session.token_hash)
        other.delete(revoked)
        other.commit()
    with pytest.raises(HTTPException) as exc:
        create_staff(db, actor, uuid4(), StaffCreate(**staff_body()))
    assert exc.value.status_code == 401
    db.rollback()


def test_rehire_uses_new_subject_clock_and_leap_day_is_policy_pending(client, db):
    headers = login(client)
    body = teaching_body(client, db, headers)
    original = db.get(EmploymentEpisode, UUID(body["episode_id"]))
    person_id = str(original.person_id)
    sources = client.get(f"/api/v1/people/staff/{person_id}/sources").json()
    membership = sources["memberships"][0]
    common = {
        "source_reference": "LOCAL_TEST_EPISODE_ORDER",
        "reason": "Synthetic permanent separation and later rehire",
    }
    response = post(
        client,
        f"/api/v1/admin/staff/{person_id}/sources",
        common
        | {
            "kind": "department",
            "id": membership["id"],
            "expected_version": membership["source_version"],
            "values": {
                "episode_id": str(original.id),
                "department_id": str(fixture_id("CSE")),
                "starts_on": "2020-07-01",
                "ends_before": "2027-01-01",
            },
        },
        headers,
    )
    assert response.status_code == 200, response.text
    response = post(
        client,
        f"/api/v1/admin/staff/{person_id}/sources",
        common
        | {
            "kind": "employment",
            "id": str(original.id),
            "expected_version": sources["episodes"][0]["source_version"],
            "values": {"starts_on": "2020-07-01", "ends_before": "2027-01-01", "is_faculty": True},
        },
        headers,
    )
    assert response.status_code == 200, response.text
    first = post(client, "/api/v1/admin/teaching", body, headers)
    assert first.status_code == 200, first.text
    rehire = post(
        client,
        f"/api/v1/admin/staff/{person_id}/sources",
        common | {"kind": "employment", "values": {"starts_on": "2027-07-01", "is_faculty": True}},
        headers,
    )
    assert rehire.status_code == 200, rehire.text
    year = db.scalar(select(AcademicYear).where(AcademicYear.starts_on == date(2027, 7, 1)))
    second = post(
        client,
        "/api/v1/admin/teaching",
        body
        | {
            "external_key": f"TEST-{uuid4().hex}",
            "episode_id": rehire.json()["id"],
            "academic_year_id": str(year.id),
            "starts_on": "2028-02-29",
            "ends_before": "2028-06-01",
        },
        headers,
    )
    assert second.status_code == 200, second.text
    view = client.get(f"/api/v1/teaching/{second.json()['id']}").json()
    assert view["first_official_date"] == "2028-02-29" and view["provisional_deadline"] is None
    assert view["deadline_policy"] == "POLICY_PENDING:P-54"
    assert (
        client.get(f"/api/v1/teaching/{first.json()['id']}").json()["first_official_date"]
        == "2026-07-10"
    )


def test_chunked_body_limit_before_multipart_processing(client):
    headers = login(client)
    response = client.post(
        "/api/v1/admin/imports",
        headers=headers | {"Content-Type": "application/octet-stream"},
        content=iter([b"x" * (3 * 1024 * 1024), b"x" * (3 * 1024 * 1024)]),
    )
    assert response.status_code == 413


def test_reference_alias_corrections_preserve_history_and_forbid_identity_merge(client, db):
    headers = login(client)
    first_subject, second_subject = subject(client, headers), subject(client, headers)
    body = {
        "kind": "alias",
        "subject_id": first_subject,
        "name": f"Synthetic alias {uuid4().hex}",
        "source_reference": "LOCAL_TEST_ALIAS",
        "reason": "Official synthetic alias mapping",
    }
    created = post(client, "/api/v1/admin/reference", body, headers)
    assert created.status_code == 200, created.text
    alias_id = created.json()["id"]
    assert (
        post(
            client,
            "/api/v1/admin/reference",
            body | {"id": alias_id, "expected_version": 1, "subject_id": second_subject},
            headers,
        ).status_code
        == 423
    )
    assert (
        post(
            client,
            "/api/v1/admin/reference",
            body | {"id": alias_id, "expected_version": 1, "name": body["name"] + " corrected"},
            headers,
        ).status_code
        == 200
    )
    history = list(
        db.scalars(select(SourceRevision).where(SourceRevision.entity_id == UUID(alias_id)))
    )
    assert len(history) == 2
    assert any(r.before and r.before["alias"] == body["name"].casefold() for r in history)


def test_teaching_name_term_filters_remain_scoped(client, db):
    headers = login(client)
    body = teaching_body(client, db, headers)
    record = post(client, "/api/v1/admin/teaching", body, headers).json()["id"]
    rows = client.get(
        "/api/v1/teaching",
        params={"q": "Local test person", "term": body["term"], "subject_id": body["subject_id"]},
    ).json()["items"]
    assert [r["id"] for r in rows] == [record]
    login(client, "faculty")
    assert (
        client.get(
            "/api/v1/teaching", params={"q": "Local test person", "subject_id": body["subject_id"]}
        ).json()["items"]
        == []
    )
