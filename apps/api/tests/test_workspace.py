"""Phase 8 register scope, retry safety, notification privacy and audited exports."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from test_people import login

from akus.models import AuditEvent, WorkJob
from akus.worker import tick
from akus.workspace.models import NoticeRead

BASE = "/api/v1"


@pytest.mark.parametrize(
    ("role", "register"),
    [
        ("faculty", "tasks"),
        ("admin", "tasks"),
        ("drc", "tasks"),
        ("hod", "tasks"),
        ("principal", "tasks"),
        ("faculty", "search"),
        ("faculty", "notifications"),
        ("drc", "drc-history"),
        ("hod", "hod-history"),
        ("hod", "department-applications"),
        ("principal", "department-applications"),
        ("principal", "applications"),
        ("principal", "departments"),
        ("principal", "topics-quotas"),
        ("principal", "exceptions"),
        ("principal", "audit"),
        ("admin", "source-audit"),
        ("admin", "operations"),
    ],
)
def test_registers_authorized_and_bounded(client, role, register):
    path = BASE + "/registers/" + register
    assert client.get(path).status_code == 401
    login(client, role)
    response = client.get(
        path, params={"limit": 1, "search": "local" if register == "search" else ""}
    )
    assert response.status_code == 200, response.text
    records = response.json()
    assert records["total"] >= len(records["items"])
    assert len(records["items"]) <= 1
    assert client.get(path, params={"limit": 101}).status_code == 422


@pytest.mark.parametrize(
    ("role", "register"),
    [
        ("faculty", "drc-history"),
        ("drc", "hod-history"),
        ("hod", "applications"),
        ("admin", "audit"),
        ("principal", "source-audit"),
        ("principal", "operations"),
        ("admin", "department-applications"),
    ],
)
def test_office_registers_deny_other_roles(client, role, register):
    h = login(client, role)
    assert client.get(BASE + "/registers/" + register).status_code == 403
    if register != "operations":
        assert (
            client.post(BASE + "/registers/" + register + "/export", headers=h, json={}).status_code
            == 403
        )


def test_notice_template_concurrency_privacy_and_replay(client, db):
    path = BASE + "/admin/notification-settings"
    h = login(client, "admin")
    current = client.get(path).json()["versions"]
    v = current[0]["version"] if current else 0
    heading = "LOCAL notice " + uuid4().hex
    body = {"heading": heading, "reason": "Template acceptance", "expected_version": v}
    assert (
        client.post(path, headers={"Idempotency-Key": str(uuid4())}, json=body).status_code == 403
    )
    first = client.post(path, headers=h, json=body)
    assert first.status_code == 200, first.text
    assert client.get(path).json()["versions"][0]["heading"] == heading
    assert first.json() == client.post(path, headers=h, json=body).json()
    assert (
        client.post(path, headers=h | {"Idempotency-Key": str(uuid4())}, json=body).status_code
        == 409
    )
    h["Idempotency-Key"] = str(uuid4())
    res = client.post(path + "/test", headers=h, json={})
    assert res.status_code == 200
    nid = res.json()["id"]
    inbox = BASE + "/registers/notifications"
    rows = client.get(inbox, params={"search": heading}).json()["items"]
    assert [(r["id"], r["status"]) for r in rows] == [(nid, "UNREAD")]
    read = BASE + "/notifications/" + nid + "/read"
    other = login(client, "faculty")
    assert client.get(inbox, params={"search": heading}).json()["total"] == 0
    assert client.post(read, headers=other, json={}).status_code == 404
    assert client.get(path).status_code == 403
    h = login(client, "admin")
    assert client.post(read, json={}).status_code == 403
    assert client.post(read, headers=h, json={}).json() == {"status": "READ"}
    assert client.post(read, headers=h, json={}).status_code == 200
    assert (
        db.scalar(
            select(func.count()).select_from(NoticeRead).where(NoticeRead.notice_id == UUID(nid))
        )
        == 1
    )
    pref = BASE + "/notifications/preference"
    assert client.post(pref, headers=h, json={"initial_filter": "UNREAD"}).status_code == 200
    assert client.get(inbox, params={"search": heading}).json()["total"] == 0
    assert client.get(inbox, params={"search": heading, "status": "ALL"}).json()["total"] == 1


def test_work_failures_backoff_and_retry_do_not_change_quota(client, db, monkeypatch):
    from akus.applications import transfers

    def fail(*args):
        raise RuntimeError("private exception message")

    monkeypatch.setattr(transfers, "worker_recheck", fail)
    j = WorkJob(kind="QUOTA_RECHECK", key="recheck:" + str(uuid4()))
    db.add(j)
    db.commit()
    jid = j.id
    factory = client.app.state.sessions
    for attempt in range(1, 4):
        with factory() as s:
            assert tick(s, jid)
            job = s.get(WorkJob, jid)
            assert job.attempts == attempt and job.last_error == "RuntimeError"
            if attempt < 3:
                assert job.state == "PENDING" and job.next_attempt_at
                s.rollback()
                assert not tick(s, jid)
                s.get(WorkJob, jid).next_attempt_at = None
                s.commit()
            else:
                assert job.state == "DEAD"
    path = BASE + "/admin/work/" + str(jid) + "/retry"
    h = login(client, "principal")
    body = {"reason": "Resolved worker dependency", "expected_attempts": 3}
    assert client.post(path, headers=h, json=body).status_code == 403
    h = login(client, "admin")
    assert client.post(path, headers=h, json=body | {"expected_attempts": 2}).status_code == 409
    assert client.post(path, headers=h, json=body).status_code == 200
    assert client.post(path, headers=h, json=body).status_code == 200
    assert (
        client.post(path, headers=h | {"Idempotency-Key": str(uuid4())}, json=body).status_code
        == 409
    )
    db.expire_all()
    assert db.get(WorkJob, jid).state == "PENDING"


def test_principal_export_records_exact_authorized_filter(client, db):
    h = login(client, "principal")
    path = BASE + "/registers/departments/export"
    assert client.post(path, json={}).status_code == 403
    response = client.post(path, json={"search": "CSE"}, headers=h)
    assert response.status_code == 200 and "attachment" in response.headers["content-disposition"]
    assert response.text.startswith("id,title,context,status,recorded_at")
    audit = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.action == "REGISTER_EXPORTED")
        .order_by(AuditEvent.recorded_at.desc())
    ).first()
    assert audit.details["register"] == "departments" and "CSE" in audit.details["filters"]


def test_own_search_does_not_disclose_others(client):
    login(client, "faculty")
    actor = client.get(BASE + "/me").json()
    for role in ("faculty", "drc"):
        login(client, role)
        found = client.get(
            BASE + "/registers/search", params={"search": actor["key"], "status": "STAFF"}
        ).json()
        assert found["total"] == (1 if role == "faculty" else 0)


def test_all_protected_contracts_reject_anonymous_requests(client):
    import re

    public = {
        "health",
        "health/live",
        "health/ready",
        "auth/config",
        "auth/google/begin",
        "auth/google/callback",
        "auth/demo-identities",
        "auth/demo-login",
    }
    for path, methods in client.get("/api/openapi.json").json()["paths"].items():
        if path.removeprefix(BASE + "/") in public:
            continue
        for method in methods:
            url = re.sub(r"\{[^}]+\}", str(uuid4()), path)
            resp = client.request(
                method,
                url,
                headers={"origin": "http://127.0.0.1:5173", "Idempotency-Key": str(uuid4())},
            )
            assert resp.status_code in {401, 403}, (method, path, resp.status_code, resp.text)


def test_review_queue_follows_next_office_and_never_self(client):
    from test_admission import draft, setup, submit

    s = setup(client, cap=3)
    faculty, h = draft(client, s)
    assert submit(client, faculty, h).status_code == 200
    drc, h = draft(client, s, role="drc")
    assert submit(client, drc, h).status_code == 200
    for role, required, hidden in [("drc", faculty, drc), ("hod", drc, faculty)]:
        login(client, role)
        path = BASE + "/applications?review=true&limit=100"
        offset = 0
        seen = set()
        while True:
            res = client.get(path + "&offset=" + str(offset)).json()
            seen.update(row["id"] for row in res["items"])
            offset += 100
            if offset >= res["total"]:
                break
        assert required in seen and hidden not in seen
    login(client, "faculty")
    assert client.get(path).status_code == 403


def test_provider_refresh_is_durable_retries_outside_transaction_and_never_accepts(
    client, db, monkeypatch
):
    from test_catalog import SOURCE, course

    from akus.catalog import provider, refresh_jobs
    from akus.catalog.models import Offering, ProviderFetch

    h = login(client, "admin")
    cid = course(client, h)
    body = {**SOURCE, "course_id": cid, "provider_id": "noc26_" + uuid4().hex[:12]}
    path = BASE + "/admin/nptel/refresh-jobs"
    other = login(client, "principal")
    assert client.post(path, headers=other, json=body).status_code == 403
    h = login(client, "admin")
    first = client.post(path, headers=h, json=body)
    assert first.status_code == 200, first.text
    assert client.post(path, headers=h, json=body).json() == first.json()
    jid = UUID(first.json()["id"])

    def unavailable(exact):
        assert exact == body["provider_id"]
        raise provider.ProviderError("PROVIDER_UNAVAILABLE")

    monkeypatch.setattr(provider, "fetch", unavailable)
    factory = client.app.state.sessions
    for attempt in range(1, 4):
        assert refresh_jobs.run_one(factory, jid)
        db.expire_all()
        job = db.get(WorkJob, jid)
        assert job.attempts == attempt and job.last_error == "PROVIDER_UNAVAILABLE"
        if attempt < 3:
            assert not refresh_jobs.run_one(factory, jid)
            job.next_attempt_at = None
            db.commit()
    assert job.state == "DEAD"
    offering = db.scalar(select(Offering).where(Offering.provider_id == body["provider_id"]))
    assert offering.current_snapshot_id is None and offering.source_status == "UNAVAILABLE"
    assert (
        db.scalar(
            select(func.count())
            .select_from(ProviderFetch)
            .where(ProviderFetch.offering_id == offering.id)
        )
        == 3
    )


def test_flagging_observation_blocks_new_admission_until_admin_source_acceptance(client):
    from test_admission import setup
    from test_catalog import SOURCE

    s = setup(client)
    offering = s["offering"]["id"]
    path = BASE + "/admin/nptel/offerings/" + offering
    read = BASE + "/nptel/offerings/" + offering
    previous = client.get(read).json()
    body = SOURCE | {
        "snapshot_id": previous["snapshot_id"],
        "expected_version": previous["version"],
    }
    h = login(client, "hod")
    assert client.post(path + "/ambiguity", json=body, headers=h).status_code == 403
    h = login(client, "admin")
    flagged = client.post(path + "/ambiguity", json=body, headers=h)
    assert flagged.status_code == 200, flagged.text
    observed = client.get(read).json()
    assert (
        observed["source_status"] == "SOURCE_CONFLICT_REVIEW_REQUIRED"
        and observed["snapshot_id"] == previous["snapshot_id"]
    )
    assert "SOURCE_MISSING_STALE_OR_UNAVAILABLE" in observed["blockers"]
    h["Idempotency-Key"] = str(uuid4())
    assert client.post(path + "/accept", json=body, headers=h).status_code == 409
    assert (
        client.post(
            path + "/accept", json=body | {"expected_version": observed["version"]}, headers=h
        ).status_code
        == 200
    )
    assert client.get(read).json()["source_status"] == "CURRENT"


@pytest.mark.parametrize("role", ["faculty", "drc", "hod", "principal", "admin"])
def test_academic_summary_resolves_current_authority_and_obligations(client, role):
    login(client, role)
    response = client.get(BASE + "/dashboard/academic")
    assert response.status_code == 200, response.text
    fields = {m["label"] for m in response.json()["metrics"]}
    assert "Open tasks in scope" in fields
    assert ("This academic year" in fields) == (role in {"faculty", "drc"})
    assert ("Counted seats across published pools" in fields) == (role in {"hod", "principal"})


def test_principal_department_compliance_cutoff(client):
    from datetime import UTC, datetime

    login(client, "principal")
    dept = client.get(BASE + "/registers/departments").json()["items"][0]["id"]
    for scope in ("institution", "department"):
        res = client.get(
            BASE + "/compliance/register",
            params={
                "scope": scope,
                "kind": "annual",
                "department": dept,
                "as_of": datetime.now(UTC).isoformat(),
            },
        )
        assert res.status_code == (200 if scope == "institution" else 403), res.text
    login(client, "hod")
    assert (
        client.get(
            BASE + "/compliance/register",
            params={"scope": "department", "kind": "annual", "department": str(uuid4())},
        ).status_code
        == 403
    )


def test_office_notice_archive_replay_and_recipient_privacy(client, db):
    from test_admission import draft, setup, submit

    from akus.applications.models import AcademicNotice
    from akus.catalog.models import AcademicEvent
    from akus.workspace import delivery

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    message = db.scalars(
        select(AcademicNotice).where(
            AcademicNotice.application_id == UUID(aid),
            AcademicNotice.kind == "APPLICATION_SUBMITTED",
        )
    ).one()
    jid = db.scalars(select(WorkJob.id).where(WorkJob.key == f"office-inbox:{message.id}")).one()
    path = BASE + "/registers/notifications"
    params = {"search": str(message.id), "status": "ALL"}
    login(client, "drc")
    assert client.get(path, params=params).json()["total"] == 0
    factory = client.app.state.sessions
    with factory() as worker:
        assert tick(worker, jid)
        assert not tick(worker, jid)
    assert client.get(path, params=params).json()["total"] == 1
    with factory.begin() as worker:
        delivery.archive(worker, worker.get(WorkJob, jid))
    assert (
        db.scalar(
            select(func.count())
            .select_from(AcademicEvent)
            .where(AcademicEvent.entity_id == message.id, AcademicEvent.kind == delivery.ARCHIVED)
        )
        == 1
    )
    for role in ("hod", "principal", "admin"):
        login(client, role)
        assert client.get(path, params=params).json()["total"] == 0
