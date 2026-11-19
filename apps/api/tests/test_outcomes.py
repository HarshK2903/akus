from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_admission import assert_balance, draft, setup, submit
from test_catalog import SOURCE, offering, post
from test_people import login

from akus.applications.models import Allocation, Application, Reconciliation
from akus.applications.outcome_models import Attempt, OutcomeFinding


def record(client, s, role="faculty", run=None, version=0):
    if not run:
        h = login(client)
        old = s["data"] | {
            "starts_on": "2025-01-15",
            "ends_on": "2025-04-15",
            "enrollment_ends_on": "2025-01-01",
            "exam_registration_ends_on": "2025-02-01",
            "scheduled_exam_on": "2025-04-30",
        }
        run = offering(client, h, s["course"], old)["id"]
    h = login(client, role)
    body = SOURCE | {
        "offering_id": run,
        "expected_version": version,
        "asserted_outcome": "NO_VALID_CERT",
        "document_digest": "a" * 64,
        "observed_at": datetime.now(UTC).isoformat(),
    }
    r = post(client, "/outcome-verifications", body, h)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def finding(client, aid, outcome="NO_VALID_CERT", role="hod", key=None, **changes):
    h = login(client, role)
    # Obtain evidence through the authorized owner's view before exercising denied roles.
    from akus.applications.outcomes import latest_evidence, latest_finding

    with client.app.state.sessions() as db:
        evidence, previous = latest_evidence(db, UUID(aid)), latest_finding(db, UUID(aid))
        body = (
            SOURCE
            | {
                "evidence_id": str(evidence.id),
                "expected_version": previous.version if previous else 0,
                "outcome": outcome,
                "concluded_on": datetime.now(UTC).date().isoformat(),
                "document_digest": "b" * 64,
                "observed_at": datetime.now(UTC).isoformat(),
                "independently_authenticated_person_and_run": True,
                "conclusive_official_result": True,
            }
            | changes
        )
    return post(client, f"/outcome-verifications/{aid}/decision", body, h, key), body, h


def approve(client, aid):
    for role, version in [("drc", 2), ("hod", 3)]:
        h = login(client, role)
        r = post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": version, "decision": "APPROVE"},
            h,
        )
        assert r.status_code == 200, r.text


def test_prior_assertion_unknown_and_unresolved_block_until_conclusive_no_certificate(client, db):
    s = setup(client)
    attempt = record(client, s)
    aid, h = draft(client, s, prior_attempt="OUTCOME_UNVERIFIED")
    assert submit(client, aid, h).status_code == 423
    assert finding(client, attempt, "UNRESOLVED")[0].status_code == 200
    h = login(client, "faculty")
    assert submit(client, aid, h).status_code == 423
    assert_balance(db, s["pool"], 0)
    assert finding(client, attempt)[0].status_code == 200
    assert_balance(db, s["pool"], 0)  # A finding never submits/reserves on anyone's behalf.
    h = login(client, "faculty")
    assert submit(client, aid, h).status_code == 200
    snap = client.get(f"/api/v1/applications/{aid}").json()["submission"]["facts"]
    latest = client.get(f"/api/v1/previous-attempts/{attempt}").json()["findings"][0]
    assert snap["prior_outcome_finding_ids"] == [latest["id"]]
    assert_balance(db, s["pool"], 1)


@pytest.mark.parametrize("role", ["faculty", "drc", "admin", "principal", "acting-hod"])
def test_outcome_decision_requires_current_independent_department_hod(client, role):
    s = setup(client)
    attempt = record(client, s)
    r, _, _ = finding(client, attempt, role=role)
    assert r.status_code == 403


def test_drc_prior_verification_is_hod_only_and_fresh_application_routes_directly(client):
    s = setup(client)
    attempt = record(client, s, "drc")
    assert finding(client, attempt)[0].status_code == 200
    aid, h = draft(client, s, "drc", prior_attempt="OUTCOME_UNVERIFIED")
    assert submit(client, aid, h).status_code == 200
    assert client.get(f"/api/v1/applications/{aid}").json()["next_office"] == "HOD"


def test_verified_certificate_blocks_repeat_despite_checkbox_or_later_claim_and_replays(client, db):
    s = setup(client)
    attempt = record(client, s)
    key = uuid4()
    r, body, h = finding(
        client,
        attempt,
        "VALID_CERT",
        key=key,
        reason="LOCAL_TEST official valid certificate at 65 percent; below Silver still blocks repeat",
    )
    assert r.status_code == 200, r.text
    replay = post(client, f"/outcome-verifications/{attempt}/decision", body, h, key)
    assert replay.status_code == 200 and replay.json() == r.json()
    aid, h = draft(client, s)
    r = submit(client, aid, h)
    assert (
        r.status_code == 409
        and r.json()["error"]["code"] == "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28"
    )
    with client.app.state.sessions() as conn:
        run = str(conn.get(Attempt, UUID(attempt)).offering_id)
    record(client, s, run=run, version=1)
    assert finding(client, attempt)[0].status_code == 423
    h = login(client, "faculty")
    assert submit(client, aid, h).status_code == 409
    assert_balance(db, s["pool"], 0)


def test_revised_assertion_requires_new_verification_without_erasing_previous_finding(client):
    s = setup(client)
    attempt = record(client, s)
    assert finding(client, attempt)[0].status_code == 200
    before = client.get(f"/api/v1/previous-attempts/{attempt}").json()
    record(client, s, run=before["offering_id"], version=1)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 423
    detail = client.get(f"/api/v1/previous-attempts/{attempt}").json()
    assert len(detail["evidence"]) == 2 and len(detail["findings"]) == 1
    assert detail["eligibility"] == "OUTCOME_PENDING"
    assert finding(client, attempt)[0].status_code == 200
    h = login(client, "faculty")
    assert submit(client, aid, h).status_code == 200


def test_retroactive_certificate_opens_q33_hold_retains_quota_and_does_not_infer_misconduct(
    client, db
):
    s = setup(client)
    attempt = record(client, s)
    assert finding(client, attempt)[0].status_code == 200
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    approve(client, aid)
    assert finding(client, attempt, "VALID_CERT")[0].status_code == 200
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == "INTEGRITY"
        )
    )
    assert case.reason == "Q33_AUTHORITY_POLICY_PENDING"
    assert case.status == "OPEN" and case.context["recognition"] == "SUSPENDED"
    h = login(client, "faculty")
    withdrawal = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": 4, "not_enrolled_declaration": True},
        h,
    )
    assert withdrawal.status_code == 423
    assert case.context["misconduct"] == "NOT_INFERRED"
    assert db.get(Application, UUID(aid)).state == "APPROVED"
    assert_balance(db, s["pool"], 1)
    assert (
        db.scalar(
            select(func.count())
            .select_from(OutcomeFinding)
            .where(OutcomeFinding.attempt_id == UUID(attempt))
        )
        == 2
    )


def test_completed_unsuccessful_approved_run_retains_count_but_allows_different_fresh_run(
    client, db
):
    s = setup(client, cap=3)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    approve(client, aid)
    attempt = record(client, s, run=s["offering"]["id"])
    # An alleged official result predating the accepted start is conflicting evidence.
    assert finding(client, attempt)[0].status_code == 423
    from test_admission import reschedule

    reschedule(
        client,
        s | {"data": s["data"] | {"starts_on": "2026-01-15"}},
        day=s["data"]["scheduled_exam_on"],
    )
    r, _, _ = finding(client, attempt)
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 1)
    assert db.get(Application, UUID(aid)).state == "OUTCOME_RECORDED"
    assert db.get(Allocation, UUID(aid)).state == "RETAINED"
    h = login(client)
    later = s | {"offering": offering(client, h, s["course"], s["data"])}
    bid, h = draft(client, later, prior_attempt="OUTCOME_UNVERIFIED")
    assert submit(client, bid, h).status_code == 200
    assert_balance(db, s["pool"], 2)
    with pytest.raises(DBAPIError):
        db.execute(text("UPDATE applications SET state='APPROVED' WHERE id=:id"), {"id": aid})
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM outcome_findings WHERE attempt_id=:id"), {"id": attempt})
    db.rollback()


def test_outcome_precision_evidence_binding_stale_version_and_private_access(client, db):
    s = setup(client)
    a, b = record(client, s), record(client, s)
    assert finding(client, a, conclusive_official_result=False)[0].status_code == 422
    assert finding(client, a, concluded_on=None)[0].status_code == 422
    assert finding(client, a)[0].status_code == 200
    r, body, h = finding(client, a, expected_version=0)
    assert r.status_code == 409
    assert post(client, f"/outcome-verifications/{b}/decision", body, h).status_code == 409
    assert (
        post(
            client, f"/outcome-verifications/{a}/decision", body, h | {"X-CSRF-Token": "bad"}
        ).status_code
        == 403
    )
    login(client, "drc")
    assert client.get(f"/api/v1/previous-attempts/{a}").status_code == 403
    login(client, "acting-hod")
    assert client.get(f"/api/v1/previous-attempts/{a}").status_code == 403
    with pytest.raises(DBAPIError):
        original = db.scalar(select(OutcomeFinding.id).where(OutcomeFinding.attempt_id == UUID(a)))
        db.execute(
            text(
                "INSERT INTO outcome_findings SELECT :id,:attempt,evidence_id,1,actor_id,office_id,outcome,concluded_on,source_reference,document_digest,observed_at,reason,now() FROM outcome_findings WHERE id=:original"
            ),
            {"id": uuid4(), "attempt": b, "original": original},
        )
    db.rollback()


def test_certificate_correction_vs_hod_final_approval_is_serialized(client, db, settings):
    from test_admission import actor_token, parallel

    from akus.applications import outcomes, service
    from akus.applications.outcome_schemas import OutcomeDecision
    from akus.applications.schemas import Review

    s = setup(client)
    attempt = record(client, s)
    assert finding(client, attempt)[0].status_code == 200
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    h = login(client, "drc")
    assert (
        post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"decision": "APPROVE", "expected_version": 2},
            h,
        ).status_code
        == 200
    )
    record_id = UUID(attempt)
    evidence = outcomes.latest_evidence(db, record_id)
    correction = OutcomeDecision.model_validate(
        SOURCE
        | {
            "evidence_id": evidence.id,
            "expected_version": 1,
            "outcome": "VALID_CERT",
            "concluded_on": "2025-05-01",
            "observed_at": datetime.now(UTC),
            "document_digest": "c" * 64,
            "independently_authenticated_person_and_run": True,
            "conclusive_official_result": True,
        }
    )
    first, second = actor_token(client, "hod"), actor_token(client, "hod")
    results = parallel(
        client,
        [
            (first, lambda c, a: outcomes.decide(c, a, uuid4(), record_id, correction)),
            (
                second,
                lambda c, a: service.review(
                    c,
                    a,
                    uuid4(),
                    UUID(aid),
                    Review.model_validate(SOURCE | {"decision": "APPROVE", "expected_version": 3}),
                    settings,
                ),
            ),
        ],
    )
    assert results[0] == "OK"
    assert_balance(db, s["pool"], 1)
    if results[1] == "OK":
        assert db.get(Application, UUID(aid)).state == "APPROVED"
        case = db.scalar(
            select(Reconciliation).where(
                Reconciliation.application_id == UUID(aid), Reconciliation.kind == "INTEGRITY"
            )
        )
        assert case.status == "OPEN" and case.context["recognition"] == "SUSPENDED"
    else:
        assert results[1] == "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28"
        assert db.get(Application, UUID(aid)).state == "UNDER_REVIEW"


def test_an_enrollment_report_on_another_draft_cannot_be_hidden_during_submission(client, db):
    from test_participation import proof

    s = setup(client)
    h = login(client)
    other = s | {"offering": offering(client, h, s["course"], s["data"])}
    a, h = draft(client, s)
    assert post(client, f"/applications/{a}/enrollment-claims", proof(), h).status_code == 200
    b, h = draft(client, other)
    r = submit(client, b, h)
    assert (
        r.status_code == 423
        and r.json()["error"]["code"] == "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29"
    )
    assert_balance(db, s["pool"], 0)
