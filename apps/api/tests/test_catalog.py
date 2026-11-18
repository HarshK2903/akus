import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException
from test_people import login

from akus.access import authority
from akus.auth import digest
from akus.catalog import provider, service
from akus.catalog.models import (
    MappingRequest,
    MappingRevision,
    Offering,
    ProviderSnapshot,
)
from akus.catalog.schemas import MappingWrite
from akus.models import AuthSession, DemoIdentity
from akus.people.seed import fixture_id
from akus.quotas.models import QuotaPool

SOURCE = {
    "source_reference": "LOCAL_TEST_OFFICIAL_FIXTURE",
    "reason": "Synthetic approved source for isolated test",
}


def post(client, path, body, headers, key=None):
    return client.post(
        "/api/v1" + path, json=body, headers=headers | {"Idempotency-Key": str(key or uuid4())}
    )


def metadata(**overrides):
    return {
        "title": "Synthetic computing",
        "description": "Local test only",
        "categories": ["Synthetic Computing", "Synthetic Data", "Synthetic Humanities"],
        "duration_weeks": 12,
        "starts_on": "2027-01-15",
        "ends_on": "2027-04-15",
        "enrollment_ends_on": "2027-01-01",
        "exam_registration_ends_on": "2027-02-01",
        "scheduled_exam_on": "2027-06-30",
    } | overrides


def course(client, headers):
    r = post(
        client,
        "/admin/nptel/courses",
        SOURCE | {"code": f"TEST-{uuid4().hex}", "title": "Synthetic stable course"},
        headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def offering(client, headers, course_id, data=None):
    r = post(
        client,
        "/admin/nptel/local-fixtures",
        SOURCE
        | {
            "course_id": course_id,
            "provider_id": f"LOCAL_{uuid4().hex}",
            "metadata": data or metadata(),
        },
        headers,
    )
    assert r.status_code == 200, r.text
    oid = r.json()["id"]
    detail = client.get(f"/api/v1/nptel/offerings/{oid}").json()
    r = post(
        client,
        f"/admin/nptel/offerings/{oid}/accept",
        SOURCE | {"snapshot_id": detail["observations"][0]["id"], "expected_version": 0},
        headers,
    )
    assert r.status_code == 200, r.text
    return client.get(f"/api/v1/nptel/offerings/{oid}").json()


def topic(client, headers, category="Synthetic Computing"):
    # Each test has a unique label and exact observed alias, avoiding global test resets.
    name = f"Synthetic topic {uuid4().hex}"
    r = post(
        client,
        "/admin/nptel/topics",
        SOURCE | {"code": f"T{uuid4().hex[:16].upper()}", "name": name},
        headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"], name


def scenario(client):
    headers = login(client)
    cid = course(client, headers)
    tid, name = topic(client, headers)
    other_id, other_name = topic(client, headers)
    data = metadata(categories=[name, other_name, "Synthetic Third"])
    view = offering(client, headers, cid, data)
    return {
        "course": cid,
        "topic": tid,
        "other_topic": other_id,
        "data": data,
        "offering": view,
        "department": str(fixture_id("department-CSE")),
    }


def mapping_body(s, version=0, **overrides):
    return (
        SOURCE
        | {
            "topic_id": s["topic"],
            "snapshot_id": s["offering"]["snapshot_id"],
            "expected_version": version,
        }
        | overrides
    )


def department(client):
    return client.get("/api/v1/nptel/context").json()["home_department_id"]


def test_catalog_separates_course_runs_and_preserves_source_history(client, db):
    s = scenario(client)
    headers = login(client)
    second = offering(client, headers, s["course"], s["data"])
    data = client.get(f"/api/v1/nptel/courses/{s['course']}").json()
    assert len(data["offerings"]) == 2
    assert second["id"] != s["offering"]["id"]
    assert data["offerings"][0]["actual_exam"] == "NOT_VERIFIED"
    assert "HOD_MAPPING_REQUIRED" in data["offerings"][0]["blockers"]
    snap = db.get(ProviderSnapshot, UUID(s["offering"]["snapshot_id"]))
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE provider_snapshots SET digest='changed' WHERE id=:id"), {"id": snap.id}
        )
    db.rollback()
    row = db.get(Offering, UUID(second["id"]))
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE nptel_offerings SET provider_id='forged' WHERE id=:id"), {"id": row.id}
        )
    db.rollback()


@pytest.mark.parametrize("role", ["faculty", "drc", "hod", "principal"])
def test_source_registry_requires_admin(client, role):
    h = login(client, role)
    r = post(
        client, "/admin/nptel/courses", SOURCE | {"code": "DENIED", "title": "Cannot create"}, h
    )
    assert r.status_code == 403


@pytest.mark.parametrize("role", ["faculty", "drc", "admin", "principal", "acting-hod"])
def test_mapping_and_quota_require_current_department_hod(client, role):
    s = scenario(client)
    login(client, "hod")
    dept = department(client)
    years = client.get("/api/v1/nptel/context").json()["years"]
    h = login(client, role)
    assert (
        post(
            client, f"/departments/{dept}/topic-mappings/{s['course']}", mapping_body(s), h
        ).status_code
        == 403
    )
    assert (
        post(
            client,
            f"/departments/{dept}/quotas",
            SOURCE
            | {
                "topic_id": s["topic"],
                "academic_year_id": years[0]["id"],
                "maximum": 5,
                "publish": True,
            },
            h,
        ).status_code
        == 403
    )


def test_mapping_requests_dedupe_without_seat_then_hod_versioned_decision(client, db):
    s = scenario(client)
    h = login(client, "faculty")
    dept = department(client)
    first = post(
        client, "/nptel/mapping-requests", SOURCE | {"offering_id": s["offering"]["id"]}, h
    )
    second = post(
        client, "/nptel/mapping-requests", SOURCE | {"offering_id": s["offering"]["id"]}, h
    )
    assert first.status_code == 200 and first.json() == second.json()
    assert (
        db.scalar(
            select(func.count())
            .select_from(QuotaPool)
            .where(QuotaPool.topic_id == UUID(s["topic"]))
        )
        == 0
    )
    h = login(client, "hod")
    path = f"/departments/{dept}/topic-mappings/{s['course']}"
    approved = post(client, path, mapping_body(s), h)
    assert approved.status_code == 200, approved.text
    assert post(client, path, mapping_body(s), h).status_code == 409
    revised = post(client, path, mapping_body(s, 1, topic_id=s["other_topic"]), h)
    assert revised.status_code == 200, revised.text
    history = client.get("/api/v1" + path).json()
    assert history["version"] == 2 and len(history["revisions"]) == 2
    assert history["revisions"][0]["valid_until"] is None and history["revisions"][1]["valid_until"]
    assert history["existing_allocation_policy"] == "POLICY_PENDING:P-NEW-11"
    old = db.get(MappingRevision, UUID(history["revisions"][1]["id"]))
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE primary_topic_mapping_revisions SET reason='forged' WHERE id=:id"),
            {"id": old.id},
        )
    db.rollback()
    assert db.get(MappingRequest, UUID(first.json()["id"])).status == "DECIDED"


def test_mapping_rejects_unobserved_category_and_alias_collisions(client):
    s = scenario(client)
    h = login(client)
    invalid, _ = topic(client, h)
    alias = f"Provider category {uuid4().hex}"
    body = SOURCE | {"topic_id": s["topic"], "label": alias}
    assert post(client, "/admin/nptel/topic-aliases", body, h).status_code == 200
    assert (
        post(
            client,
            "/admin/nptel/topic-aliases",
            body | {"topic_id": invalid, "label": alias.upper()},
            h,
        ).status_code
        == 423
    )
    h = login(client, "hod")
    dept = department(client)
    assert (
        post(
            client,
            f"/departments/{dept}/topic-mappings/{s['course']}",
            mapping_body(s, topic_id=invalid),
            h,
        ).status_code
        == 422
    )


def test_annual_pools_independent_publish_revision_and_idempotence(client, db):
    s = scenario(client)
    h = login(client, "hod")
    dept = department(client)
    years = client.get("/api/v1/nptel/context").json()["years"]
    body = SOURCE | {"topic_id": s["topic"], "academic_year_id": years[0]["id"], "maximum": 5}
    key = uuid4()
    first = post(client, f"/departments/{dept}/quotas", body, h, key)
    assert first.status_code == 200, first.text
    assert post(client, f"/departments/{dept}/quotas", body, h, key).json() == first.json()
    assert client.get(f"/api/v1/quotas/{first.json()['id']}").json()["available"] is None
    publish = post(
        client, f"/departments/{dept}/quotas", body | {"publish": True, "expected_version": 1}, h
    )
    assert publish.status_code == 200, publish.text
    second = post(
        client,
        f"/departments/{dept}/quotas",
        body | {"academic_year_id": years[1]["id"], "maximum": 2, "publish": True},
        h,
    )
    assert second.status_code == 200, second.text
    assert client.get(f"/api/v1/quotas/{first.json()['id']}").json()["maximum"] == 5
    assert (
        post(client, f"/departments/{dept}/quotas", body | {"expected_version": 2}, h).status_code
        == 409
    )
    assert len(client.get(f"/api/v1/quotas/{first.json()['id']}").json()["history"]) == 2


def raw_preview(**patch):
    c = {
        "title": "Synthetic provider course",
        "about": "<p>Safe description</p><script>bad()</script>",
        "category_name": ["COMP_SCI_ENGG", "Domain_15"],
        "weeks": 12,
        "start_date": "2026-07-19T18:30:00Z",
        "end_date": "2026-10-08T18:30:00Z",
        "enrollment_end_date": "2026-08-03T18:29:00Z",
        "exam_registration_end_date": "2026-08-17T18:29:00Z",
        "exam_date": "2026-10-15T18:30:00Z",
    } | patch
    return json.dumps(
        {
            "status": 200,
            "payload": json.dumps(
                {
                    "course_info": {"_reserved": {"context_path": "noc26_cs98"}, "course": c},
                    "is_enrolled": True,
                }
            ),
        }
    ).encode()


def test_provider_actual_envelope_dates_and_plain_text():
    m = provider.parse(raw_preview(), "noc26_cs98")
    assert str(m.starts_on) == "2026-07-20" and str(m.scheduled_exam_on) == "2026-10-16"
    assert str(m.enrollment_ends_on) == "2026-08-03"
    assert m.categories == ["COMP_SCI_ENGG", "Domain_15"]
    assert m.description == "Safe description" and "is_enrolled" not in m.model_dump()


@pytest.mark.parametrize(
    "patch",
    [
        {"category_name": []},
        {"category_name": "wrong"},
        {"weeks": "nonsense"},
        {"exam_date": "bad"},
        {"title": ""},
        {"category_name": ["<script>"]},
    ],
)
def test_provider_schema_changes_fail_closed(patch):
    with pytest.raises(provider.ProviderError):
        provider.parse(raw_preview(**patch), "noc26_cs98")


def test_provider_unavailable_records_failure_and_blocks_readiness(client, monkeypatch):
    h = login(client)
    cid = course(client, h)
    monkeypatch.setattr(
        provider,
        "fetch",
        lambda _: (_ for _ in ()).throw(provider.ProviderError("PROVIDER_UNAVAILABLE")),
    )
    response = post(
        client,
        "/admin/nptel/provider-fetches",
        SOURCE | {"course_id": cid, "provider_id": f"noc26_test{uuid4().hex[:12]}"},
        h,
    )
    assert response.status_code == 200, response.text
    view = client.get(f"/api/v1/nptel/offerings/{response.json()['id']}").json()
    assert view["source_status"] == "UNAVAILABLE" and view["snapshot_id"] is None
    assert view["fetches"][0]["error"] == "PROVIDER_UNAVAILABLE"


def test_mapping_two_writers_one_effective_revision(client, db, settings):
    s = scenario(client)
    login(client, "hod")
    dept = department(client)
    session_hash = digest(client.cookies.get("akus_demo_session"))
    barrier = Barrier(2)

    def writer(index):
        with client.app.state.sessions() as conn:
            session = conn.get(AuthSession, session_hash)
            actor = authority(conn, conn.get(DemoIdentity, session.identity_id), session)
            barrier.wait(timeout=10)
            try:
                service.write_mapping(
                    conn,
                    actor,
                    uuid4(),
                    UUID(dept),
                    UUID(s["course"]),
                    MappingWrite.model_validate(
                        mapping_body(s, topic_id=s["other_topic"] if index else s["topic"])
                    ),
                    settings,
                )
                return "OK"
            except HTTPException as e:
                conn.rollback()
                return e.detail

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(writer, range(2)))
    assert sorted(outcomes) == ["OK", "VERSION_CONFLICT"]
