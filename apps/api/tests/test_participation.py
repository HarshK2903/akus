from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_admission import DECLARATIONS, assert_balance, draft, reschedule, setup, submit, target
from test_catalog import SOURCE, post
from test_people import login

from akus.applications import service
from akus.applications.models import Application, Ledger, Reconciliation
from akus.applications.workflow_models import (
    DraftRevision,
    EnrollmentClaim,
    EnrollmentFinding,
    WithdrawalDecision,
)


def proof(**overrides):
    now = datetime.now(UTC).isoformat()
    return (
        SOURCE
        | {
            "expected_version": 0,
            "enrolled_at": now,
            "document_digest": "d" * 64,
            "observed_at": now,
        }
        | overrides
    )


def claimed(client, s=None):
    s = s or setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    body = proof()
    r = post(client, f"/applications/{aid}/enrollment-claims", body, h)
    assert r.status_code == 200, r.text
    return s, aid, body


def verified(client, aid, body, **changes):
    h = login(client, "hod")
    details = client.get(f"/api/v1/applications/{aid}").json()["participation"]
    r = post(
        client,
        f"/applications/{aid}/verify-enrollment",
        body
        | {
            "claim_id": details["claims"][0]["id"],
            "outcome": "VERIFIED",
            "independently_authenticated": True,
        }
        | changes,
        h,
    )
    assert r.status_code == 200, r.text
    return h


def withdrawal_request(client, aid):
    h = login(client, "faculty")
    app = client.get(f"/api/v1/applications/{aid}").json()
    r = post(
        client,
        f"/applications/{aid}/withdrawal-requests",
        SOURCE | {"expected_version": app["version"], "voluntary_request": True},
        h,
    )
    assert r.status_code == 200, r.text
    return client.get(f"/api/v1/applications/{aid}").json()["participation"]["pending_withdrawal"][
        "id"
    ]


def authorize(client, aid, request_id, key=None, **changes):
    h = login(client, "hod")
    app = client.get(f"/api/v1/applications/{aid}").json()
    body = (
        SOURCE
        | {
            "request_id": request_id,
            "expected_version": app["version"],
            "decision": "AUTHORIZE",
            "independently_checked": True,
        }
        | changes
    )
    return post(client, f"/applications/{aid}/withdrawal-decision", body, h, key), body, h


def test_draft_revisions_and_required_academic_relevance(client, db):
    s = setup(client)
    aid, h = draft(client, s, academic_relevance="")
    r = submit(client, aid, h)
    assert r.status_code == 422 and r.json()["error"]["code"] == "ACADEMIC_RELEVANCE_REQUIRED"
    body = {
        "id": aid,
        "offering_id": s["offering"]["id"],
        "expected_version": 1,
        "declarations": DECLARATIONS,
    }
    r = post(client, "/applications", body, h)
    assert r.status_code == 200, r.text
    assert post(client, "/applications", body, h).status_code == 409
    rows = list(
        db.scalars(
            select(DraftRevision)
            .where(DraftRevision.application_id == UUID(aid))
            .order_by(DraftRevision.version)
        )
    )
    assert [r.version for r in rows] == [1, 2]
    assert rows[0].declarations["academic_relevance"] == ""
    assert rows[1].declarations["academic_relevance"] == DECLARATIONS["academic_relevance"]
    with pytest.raises(DBAPIError):
        db.execute(
            text("DELETE FROM application_draft_revisions WHERE application_id=:id"), {"id": aid}
        )
    db.rollback()
    assert_balance(db, s["pool"], 0)


def test_unverified_enrollment_prevents_bypass_and_late_verified_path_allows_actual_route(
    client, db, monkeypatch
):
    s, aid, body = claimed(client)
    h = login(client, "drc")
    decision = SOURCE | {"expected_version": 2, "decision": "APPROVE"}
    assert post(client, f"/applications/{aid}/review", decision, h).status_code == 423
    verified(client, aid, body)
    monkeypatch.setattr(service, "today", lambda: date(2027, 1, 2))
    for role, version in [("drc", 2), ("hod", 3)]:
        h = login(client, role)
        r = post(client, f"/applications/{aid}/review", decision | {"expected_version": version}, h)
        assert r.status_code == 200, r.text
    assert db.get(Application, UUID(aid)).state == "APPROVED"
    assert_balance(db, s["pool"], 1)


@pytest.mark.parametrize("role", ["faculty", "drc", "admin", "principal", "acting-hod"])
def test_only_current_distinct_department_hod_verifies_enrollment(client, role):
    _, aid, body = claimed(client)
    claim_id = client.get(f"/api/v1/applications/{aid}").json()["participation"]["claims"][0]["id"]
    h = login(client, role)
    r = post(
        client,
        f"/applications/{aid}/verify-enrollment",
        body | {"claim_id": claim_id, "outcome": "VERIFIED", "independently_authenticated": True},
        h,
    )
    assert r.status_code == 403


def test_date_only_same_day_is_ambiguous_and_retains_seat(client, db):
    s, aid, body = claimed(client)
    from zoneinfo import ZoneInfo

    body = body | {
        "enrolled_at": None,
        "enrolled_on": datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat(),
    }
    verified(client, aid, body)
    a = client.get(f"/api/v1/applications/{aid}").json()
    assert a["participation"]["findings"][0]["chronology"] == "INDETERMINATE_SAME_DAY"
    assert not a["participation"]["verified_submission_first"]
    request = withdrawal_request(client, aid)
    assert authorize(client, aid, request)[0].status_code == 423
    assert_balance(db, s["pool"], 1)


def test_q04_release_uses_transferred_pool_and_replays_exactly_once(client, db):
    s, aid, body = claimed(client)
    verified(client, aid, body)
    request = withdrawal_request(client, aid)
    dest = target(client, s)
    reschedule(client, s)
    key = uuid4()
    response, decision, headers = authorize(client, aid, request, key=key)
    assert response.status_code == 200, response.text
    replay = post(client, f"/applications/{aid}/withdrawal-decision", decision, headers, key)
    assert replay.status_code == 200 and replay.json() == response.json()
    assert (
        post(client, f"/applications/{aid}/withdrawal-decision", decision, headers).status_code
        == 409
    )
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 0)
    movement = db.scalar(
        select(Ledger).where(
            Ledger.application_id == UUID(aid), Ledger.kind == "HOD_WITHDRAW_RELEASE"
        )
    )
    assert movement.pool_id == UUID(dest)
    assert db.scalar(select(func.count()).select_from(WithdrawalDecision)) >= 1
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM enrollment_findings WHERE application_id=:id"), {"id": aid})
    db.rollback()


def test_known_enrollment_cannot_be_hidden_by_unenrolled_checkbox_or_new_draft(client, db):
    s, aid, body = claimed(client)
    h = login(client, "faculty")
    r = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
        h,
    )
    assert r.status_code == 423
    h = login(client, "drc")
    assert (
        post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": 2, "decision": "REJECT"},
            h,
        ).status_code
        == 200
    )
    bid, h = draft(client, s)
    r = submit(client, bid, h)
    assert (
        r.status_code == 409
        and r.json()["error"]["code"] == "NPTEL_FIRST_ENROLLMENT_PROHIBITED_Q21"
    )
    assert_balance(db, s["pool"], 0)


def test_q04_after_start_and_unverified_request_never_release(client, db, monkeypatch):
    s, aid, body = claimed(client)
    request = withdrawal_request(client, aid)
    assert authorize(client, aid, request)[0].status_code == 423
    verified(client, aid, body)
    monkeypatch.setattr(service, "today", lambda: date(2027, 2, 1))
    r = authorize(client, aid, request)[0]
    assert (
        r.status_code == 423
        and r.json()["error"]["code"] == "POST_START_WITHDRAWAL_RETAINS_QUOTA_Q05"
    )
    assert_balance(db, s["pool"], 1)


def test_early_enrollment_after_approval_opens_integrity_hold_without_releasing(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    for role, version in [("drc", 2), ("hod", 3)]:
        h = login(client, role)
        assert (
            post(
                client,
                f"/applications/{aid}/review",
                SOURCE | {"expected_version": version, "decision": "APPROVE"},
                h,
            ).status_code
            == 200
        )
    h = login(client, "faculty")
    body = proof(enrolled_at=(datetime.now(UTC) - timedelta(days=1)).isoformat())
    assert post(client, f"/applications/{aid}/enrollment-claims", body, h).status_code == 200
    verified(client, aid, body)
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == "INTEGRITY"
        )
    )
    assert case.status == "OPEN" and case.context["recognition"] == "SUSPENDED"
    assert db.get(Application, UUID(aid)).state == "APPROVED"
    assert_balance(db, s["pool"], 1)


def test_enrollment_version_csrf_and_cross_application_binding(client, db):
    s, aid, body = claimed(client)
    bid, h = draft(client, s, "drc")
    assert submit(client, bid, h).status_code == 200
    verified(client, aid, body)
    claim_id = db.scalar(
        select(EnrollmentClaim.id).where(EnrollmentClaim.application_id == UUID(aid))
    )
    h = login(client, "hod")
    payload = body | {
        "claim_id": str(claim_id),
        "outcome": "VERIFIED",
        "independently_authenticated": True,
    }
    assert post(client, f"/applications/{bid}/verify-enrollment", payload, h).status_code == 409
    assert (
        client.post(
            f"/api/v1/applications/{aid}/verify-enrollment",
            json=payload,
            headers={"Origin": "http://127.0.0.1:5173", "Idempotency-Key": str(uuid4())},
        ).status_code
        == 403
    )
    with pytest.raises(DBAPIError):
        finding = db.scalar(
            select(EnrollmentFinding).where(EnrollmentFinding.application_id == UUID(aid))
        )
        db.execute(
            text(
                "INSERT INTO enrollment_findings SELECT :new_id,:other_app,claim_id,2,outcome,actor_id,office_id,enrolled_at,enrolled_on,source_reference,document_digest,observed_at,reason,now() FROM enrollment_findings WHERE id=:id"
            ),
            {"new_id": uuid4(), "other_app": bid, "id": finding.id},
        )
    db.rollback()


def test_q04_withdrawal_vs_transfer_releases_authoritative_pool_once(client, db, settings):
    from test_admission import actor_token, observe, parallel

    from akus.applications import participation
    from akus.applications.models import Allocation
    from akus.applications.participation_schemas import DecideWithdrawal
    from akus.catalog import service as catalog
    from akus.catalog.schemas import SnapshotAccept

    s, aid, evidence = claimed(client)
    verified(client, aid, evidence)
    request = withdrawal_request(client, aid)
    dest = target(client, s)
    _, offering, body = observe(client, s)
    admin, hod = actor_token(client, "admin"), actor_token(client, "hod")
    results = parallel(
        client,
        [
            (
                admin,
                lambda conn, actor: catalog.accept_snapshot(
                    conn,
                    actor,
                    uuid4(),
                    UUID(offering["id"]),
                    SnapshotAccept.model_validate(body),
                    settings,
                ),
            ),
            (
                hod,
                lambda conn, actor: participation.decide_withdrawal(
                    conn,
                    actor,
                    uuid4(),
                    UUID(aid),
                    DecideWithdrawal.model_validate(
                        SOURCE
                        | {
                            "request_id": request,
                            "expected_version": 2,
                            "decision": "AUTHORIZE",
                            "independently_checked": True,
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
    allocation = db.get(Allocation, UUID(aid))
    releases = list(
        db.scalars(
            select(Ledger).where(
                Ledger.application_id == UUID(aid), Ledger.kind == "HOD_WITHDRAW_RELEASE"
            )
        )
    )
    assert allocation.state == "RELEASED"
    assert len(releases) == 1 and releases[0].pool_id == allocation.pool_id


def test_q25_withdrawn_same_run_cannot_reapply_after_start_despite_open_enrollment(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    assert (
        post(
            client,
            f"/applications/{aid}/withdraw",
            SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
            h,
        ).status_code
        == 200
    )
    changed = s["data"] | {"starts_on": "2026-01-01"}
    from test_admission import observe

    h, d, body = observe(client, s | {"data": changed}, day="2027-06-30")
    assert post(client, f"/admin/nptel/offerings/{d['id']}/accept", body, h).status_code == 200
    bid, h = draft(client, s)
    response = submit(client, bid, h)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REAPPLICATION_AFTER_COMMENCEMENT_PROHIBITED_Q25"
    assert_balance(db, s["pool"], 0)


def test_q19_late_official_extension_requires_final_hod_and_current_evidence(
    client, db, monkeypatch
):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    monkeypatch.setattr(service, "today", lambda: date(2027, 1, 3))
    extension = {
        "valid_through": "2027-01-04",
        "observed_at": datetime.now(UTC).isoformat(),
        "independently_checked": True,
        "document_digest": "a" * 64,
    }
    decision = SOURCE | {"expected_version": 2, "decision": "APPROVE"}
    h = login(client, "drc")
    assert client.get(f"/api/v1/applications/{aid}").json()["enrollment_deadline_passed"]
    assert (
        post(
            client, f"/applications/{aid}/review", decision | {"enrollment_extension": extension}, h
        ).status_code
        == 403
    )
    assert post(client, f"/applications/{aid}/review", decision, h).status_code == 200
    h = login(client, "hod")
    decision["expected_version"] = 3
    assert post(client, f"/applications/{aid}/review", decision, h).status_code == 423
    assert (
        post(
            client,
            f"/applications/{aid}/review",
            decision | {"enrollment_extension": extension | {"valid_through": "2027-01-02"}},
            h,
        ).status_code
        == 423
    )
    assert_balance(db, s["pool"], 1)
    assert (
        post(
            client, f"/applications/{aid}/review", decision | {"enrollment_extension": extension}, h
        ).status_code
        == 200
    )
    from akus.applications.workflow_models import ReviewDecision

    fact = db.scalar(
        select(ReviewDecision).where(
            ReviewDecision.application_id == UUID(aid), ReviewDecision.stage == "HOD"
        )
    )
    assert fact.facts["enrollment_extension"]["document_digest"] == extension["document_digest"]


@pytest.mark.parametrize("closure", ["REJECT", "WITHDRAW"])
def test_q24_q25_fresh_eligible_application_keeps_original_history(client, db, closure):
    s = setup(client, cap=1)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    if closure == "REJECT":
        response = post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": 2, "decision": "REJECT"},
            login(client, "drc"),
        )
    else:
        response = post(
            client,
            f"/applications/{aid}/withdraw",
            SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
            h,
        )
    assert response.status_code == 200, response.text
    assert_balance(db, s["pool"], 0)
    bid, h = draft(client, s)
    assert bid != aid and submit(client, bid, h).status_code == 200
    assert_balance(db, s["pool"], 1)
    assert db.get(Application, UUID(aid)).state == (
        "REJECTED" if closure == "REJECT" else "WITHDRAWN"
    )
    assert db.get(Application, UUID(bid)).next_office == "DRC_HEAD"


def test_q26_distinct_active_courses_per_faculty(client, db):
    a, b = setup(client), setup(client)
    for s in [a, b]:
        aid, h = draft(client, s)
        assert submit(client, aid, h).status_code == 200
        assert_balance(db, s["pool"], 1)
