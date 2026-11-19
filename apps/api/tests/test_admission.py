from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException
from test_catalog import SOURCE, course, department, mapping_body, offering, post, scenario
from test_people import login

from akus.access import authority
from akus.applications import service
from akus.applications.models import Allocation, Application, Ledger, Reconciliation, Submission
from akus.applications.schemas import Submit
from akus.auth import digest
from akus.models import AuthSession, DemoIdentity
from akus.quotas.models import QuotaPool

DECLARATIONS = {
    "academic_relevance": "LOCAL_TEST alignment with official teaching and department subject knowledge",
    "score_sharing_yes": True,
    "not_yet_enrolled": True,
    "prior_attempt": "NONE_DECLARED",
    "emerging_technology_exception": False,
    "acknowledgement": True,
}


def setup(client, cap=2, published=True):
    s = scenario(client)
    h = login(client, "hod")
    dept = department(client)
    ctx = client.get("/api/v1/nptel/context").json()
    year = next(y["id"] for y in ctx["years"] if y["starts_on"] == "2026-07-01")
    next_year = next(y["id"] for y in ctx["years"] if y["starts_on"] == "2027-07-01")
    r = post(client, f"/departments/{dept}/topic-mappings/{s['course']}", mapping_body(s), h)
    assert r.status_code == 200, r.text
    r = post(
        client,
        f"/departments/{dept}/quotas",
        SOURCE
        | {"topic_id": s["topic"], "academic_year_id": year, "maximum": cap, "publish": published},
        h,
    )
    assert r.status_code == 200, r.text
    s |= {"dept": dept, "year": year, "next_year": next_year, "pool": r.json()["id"]}
    return s


def draft(client, s, role="faculty", **declarations):
    # Independent browser session: signing in again must not revoke a race participant.
    client.cookies.clear()
    h = login(client, role)
    r = post(
        client,
        "/applications",
        {"offering_id": s["offering"]["id"], "declarations": DECLARATIONS | declarations},
        h,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"], h


def submit(client, aid, h, key=None):
    detail = client.get("/api/v1/applications/" + aid).json()
    source = detail["offering"]
    return post(
        client,
        f"/applications/{aid}/submit",
        {
            "expected_version": detail["version"],
            "snapshot_id": source["snapshot_id"],
            "mapping_revision_id": source["mapping_revision_id"],
        },
        h,
        key,
    )


def target(client, s, cap=2, publish=True):
    h = login(client, "hod")
    r = post(
        client,
        f"/departments/{s['dept']}/quotas",
        SOURCE
        | {
            "topic_id": s["topic"],
            "academic_year_id": s["next_year"],
            "maximum": cap,
            "publish": publish,
        },
        h,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def observe(client, s, day="2027-07-15"):
    client.cookies.clear()
    h = login(client)
    r = post(
        client,
        "/admin/nptel/local-fixtures",
        SOURCE
        | {
            "course_id": s["course"],
            "provider_id": s["offering"]["provider_id"],
            "metadata": s["data"] | {"scheduled_exam_on": day},
        },
        h,
    )
    assert r.status_code == 200, r.text
    d = client.get("/api/v1/nptel/offerings/" + s["offering"]["id"]).json()
    return (
        h,
        d,
        {"expected_version": d["version"], "snapshot_id": d["observations"][0]["id"]} | SOURCE,
    )


def reschedule(client, s, day="2027-07-15"):
    h, d, body = observe(client, s, day)
    r = post(client, f"/admin/nptel/offerings/{d['id']}/accept", body, h)
    assert r.status_code == 200, r.text
    return body


def actor_token(client, role):
    client.cookies.clear()
    login(client, role)
    return digest(client.cookies.get("akus_demo_session"))


def run_actor(client, token, fn):
    with client.app.state.sessions() as db:
        session = db.get(AuthSession, token)
        actor = authority(db, db.get(DemoIdentity, session.identity_id), session)
        try:
            fn(db, actor)
            return "OK"
        except HTTPException as e:
            db.rollback()
            return e.detail


def assert_balance(db, pool_id, expected):
    db.expire_all()
    pool = db.get(QuotaPool, UUID(pool_id))
    assert pool.occupied == expected
    assert (
        db.scalar(select(func.coalesce(func.sum(Ledger.delta), 0)).where(Ledger.pool_id == pool.id))
        == expected
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(Allocation)
            .where(Allocation.pool_id == pool.id, Allocation.state != "RELEASED")
        )
        == expected
    )


def test_draft_and_missing_mapping_never_reserve(client, db):
    s = scenario(client)
    aid, h = draft(client, s)
    r = submit(client, aid, h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "HOD_MAPPING_REQUIRED"
    assert db.get(Application, UUID(aid)).state == "DRAFT"
    assert db.get(Allocation, UUID(aid)) is None


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"score_sharing_yes": False}, "SCORE_SHARING_AND_DECLARATIONS_REQUIRED"),
        ({"not_yet_enrolled": False}, "NPTEL_FIRST_ENROLLMENT_PROHIBITED_Q21"),
        ({"prior_attempt": "OUTCOME_UNVERIFIED"}, "PRIOR_OUTCOME_VERIFICATION_REQUIRED_Q29"),
        ({"prior_attempt": "VALID_CERTIFICATE"}, "CANONICAL_COURSE_REPEAT_PROHIBITED_Q28"),
        ({"emerging_technology_exception": True}, "EMERGING_TECH_AUTHORITY_POLICY_PENDING"),
    ],
)
def test_eligibility_failures_preserve_draft(client, db, changes, code):
    s = setup(client)
    aid, h = draft(client, s, **changes)
    r = submit(client, aid, h)
    assert r.json()["error"]["code"] == code, r.text
    assert_balance(db, s["pool"], 0)


@pytest.mark.parametrize("role", ["hod", "acting-hod", "principal", "admin"])
def test_only_eligible_applicants_can_create_drafts(client, role):
    s = setup(client)
    h = login(client, role)
    r = post(
        client,
        "/applications",
        {"offering_id": s["offering"]["id"], "declarations": DECLARATIONS},
        h,
    )
    assert r.status_code == 403


def test_submission_idempotent_immutable_snapshot_and_ordinary_route(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    before = client.get("/api/v1/applications/" + aid).json()
    body = {
        "expected_version": 1,
        "snapshot_id": before["offering"]["snapshot_id"],
        "mapping_revision_id": before["offering"]["mapping_revision_id"],
    }
    key = uuid4()
    first = post(client, f"/applications/{aid}/submit", body, h, key)
    assert first.status_code == 200, first.text
    assert post(client, f"/applications/{aid}/submit", body, h, key).json() == first.json()
    assert_balance(db, s["pool"], 1)
    saved = db.get(Submission, UUID(aid))
    assert saved.facts["route"] == ["DRC_HEAD", "HOD"]
    assert saved.facts["academic_year"] == "2026–27" or saved.facts["academic_year"] == "2026-27"
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE application_submissions SET facts='{}' WHERE application_id=:id"),
            {"id": aid},
        )
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE department_topic_quotas SET occupied=0 WHERE id=:id"), {"id": s["pool"]}
        )
        db.commit()
    db.rollback()


def test_unpublished_pool_and_full_pool_are_not_successful_submissions(client, db):
    s = setup(client, 0, False)
    aid, h = draft(client, s)
    assert submit(client, aid, h).json()["error"]["code"] == "PUBLISHED_ANNUAL_QUOTA_REQUIRED"
    hh = login(client, "hod")
    assert (
        post(
            client,
            f"/departments/{s['dept']}/quotas",
            SOURCE
            | {
                "topic_id": s["topic"],
                "academic_year_id": s["year"],
                "maximum": 0,
                "publish": True,
                "expected_version": 1,
            },
            hh,
        ).status_code
        == 200
    )
    h = login(client, "faculty")
    assert submit(client, aid, h).json()["error"]["code"] == "QUOTA_FULL"
    assert_balance(db, s["pool"], 0)


def test_drc_direct_hod_and_reviewer_scope_with_rejection_release(client, db):
    s = setup(client)
    aid, h = draft(client, s, "drc")
    assert submit(client, aid, h).status_code == 200
    d = client.get("/api/v1/applications/" + aid).json()
    assert d["next_office"] == "HOD" and d["submission"]["facts"]["route"] == ["HOD"]
    for role in ["drc", "principal", "admin", "acting-hod"]:
        hh = login(client, role)
        r = post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": 2, "decision": "REJECT"},
            hh,
        )
        assert r.status_code == 403, r.text
    hh = login(client, "hod")
    r = post(
        client,
        f"/applications/{aid}/review",
        SOURCE | {"expected_version": 2, "decision": "REJECT"},
        hh,
    )
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 0)
    assert db.get(Allocation, UUID(aid)).state == "RELEASED"


def test_two_stage_review_confirms_one_seat(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    h = login(client, "hod")
    assert (
        post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": 2, "decision": "APPROVE"},
            h,
        ).status_code
        == 403
    )
    h = login(client, "drc")
    assert (
        post(
            client,
            f"/applications/{aid}/review",
            SOURCE | {"expected_version": 2, "decision": "APPROVE"},
            h,
        ).status_code
        == 200
    )
    h = login(client, "hod")
    r = post(
        client,
        f"/applications/{aid}/review",
        SOURCE | {"expected_version": 3, "decision": "APPROVE"},
        h,
    )
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 1)
    assert db.get(Allocation, UUID(aid)).state == "CONFIRMED"


@pytest.mark.parametrize("mode", ["missing", "unpublished", "full"])
def test_blocked_transfer_retains_source_then_authorized_recheck(client, db, mode):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = (
        target(client, s, 0 if mode == "full" else 2, mode != "unpublished")
        if mode != "missing"
        else None
    )
    reschedule(client, s)
    assert_balance(db, s["pool"], 1)
    if dest:
        assert_balance(db, dest, 0)
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == "QUOTA_TRANSFER"
        )
    )
    assert case.status == "OPEN"
    assert (
        case.reason
        == {
            "missing": "TARGET_QUOTA_MISSING",
            "unpublished": "TARGET_QUOTA_UNPUBLISHED",
            "full": "TARGET_QUOTA_FULL",
        }[mode]
    )
    for role in ("hod", "principal"):
        login(client, role)
        detail = client.get(f"/api/v1/quota-transfer-cases/{case.id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["id"] == aid
    for role in ("faculty", "acting-hod", "admin"):
        login(client, role)
        assert client.get(f"/api/v1/quota-transfer-cases/{case.id}").status_code == 403
    h = login(client, "hod")
    r = post(
        client,
        f"/departments/{s['dept']}/quotas",
        SOURCE
        | {
            "topic_id": s["topic"],
            "academic_year_id": s["next_year"],
            "maximum": 2,
            "publish": True,
            "expected_version": 1 if dest else 0,
        },
        h,
    )
    assert r.status_code == 200, r.text
    dest = r.json()["id"]
    for _ in range(2):
        assert post(client, f"/applications/{aid}/reconcile", SOURCE, h).status_code == 200
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 1)
    db.refresh(case)
    assert case.status == "RESOLVED"
    assert (
        db.scalar(
            select(func.count())
            .select_from(Ledger)
            .where(Ledger.application_id == UUID(aid), Ledger.kind == "TRANSFER")
        )
        == 2
    )


def test_transfer_roundtrip_stale_same_year_and_current_pool_release(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s)
    reschedule(client, s)
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 1)
    reschedule(client, s, "2027-07-20")
    assert_balance(db, dest, 1)
    h = login(client)
    d = client.get("/api/v1/nptel/offerings/" + s["offering"]["id"]).json()
    r = post(
        client,
        f"/admin/nptel/offerings/{d['id']}/accept",
        SOURCE | {"snapshot_id": s["offering"]["snapshot_id"], "expected_version": d["version"]},
        h,
    )
    assert r.status_code == 409 and r.json()["error"]["code"] == "STALE_PROVIDER_EVENT"
    reschedule(client, s, "2027-06-25")
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 0)
    reschedule(client, s)
    h = login(client, "faculty")
    r = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
        h,
    )
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 0)
    assert db.get(Submission, UUID(aid)).original_pool_id == UUID(s["pool"])
    assert db.get(Allocation, UUID(aid)).pool_id == UUID(dest)
    reschedule(client, s, "2027-06-26")
    assert_balance(db, s["pool"], 0)


def test_last_shared_seat_race_across_distinct_courses(client, db, settings):
    s = setup(client, 1)
    h = login(client)
    cid = course(client, h)
    second = s | {"course": cid, "offering": offering(client, h, cid, s["data"])}
    h = login(client, "hod")
    assert (
        post(
            client, f"/departments/{s['dept']}/topic-mappings/{cid}", mapping_body(second), h
        ).status_code
        == 200
    )
    items = []
    for scenario_, role in [(s, "faculty"), (second, "drc")]:
        aid, _ = draft(client, scenario_, role)
        d = client.get("/api/v1/applications/" + aid).json()
        items.append(
            (
                aid,
                digest(client.cookies.get("akus_demo_session")),
                Submit(
                    expected_version=1,
                    snapshot_id=d["offering"]["snapshot_id"],
                    mapping_revision_id=d["offering"]["mapping_revision_id"],
                ),
            )
        )
    barrier = Barrier(2)

    def writer(item):
        aid, token, body = item

        def work(conn, actor):
            barrier.wait(timeout=10)
            service.submit(conn, actor, uuid4(), UUID(aid), body, settings)

        return run_actor(client, token, work)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, items))
    assert sorted(results) == ["OK", "QUOTA_FULL"]
    assert_balance(db, s["pool"], 1)


def parallel(client, tasks):
    barrier = Barrier(len(tasks))

    def execute(task):
        token, fn = task

        def synchronized(conn, actor):
            barrier.wait(timeout=10)
            fn(conn, actor)

        return run_actor(client, token, synchronized)

    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        return list(pool.map(execute, tasks))


def submit_body(client, aid):
    d = client.get("/api/v1/applications/" + aid).json()
    return Submit(
        expected_version=d["version"],
        snapshot_id=d["offering"]["snapshot_id"],
        mapping_revision_id=d["offering"]["mapping_revision_id"],
    )


def test_two_offerings_same_person_canonical_race(client, db, settings):
    s = setup(client, 5)
    h = login(client)
    second = s | {"offering": offering(client, h, s["course"], s["data"])}
    aid, _ = draft(client, s)
    body1 = submit_body(client, aid)
    token1 = digest(client.cookies.get("akus_demo_session"))
    bid, _ = draft(client, second)
    body2 = submit_body(client, bid)
    token2 = digest(client.cookies.get("akus_demo_session"))
    results = parallel(
        client,
        [
            (
                token1,
                lambda conn, actor: service.submit(
                    conn, actor, uuid4(), UUID(aid), body1, settings
                ),
            ),
            (
                token2,
                lambda conn, actor: service.submit(
                    conn, actor, uuid4(), UUID(bid), body2, settings
                ),
            ),
        ],
    )
    assert sorted(results) == ["ACTIVE_CANONICAL_COURSE_APPLICATION_EXISTS", "OK"]
    assert_balance(db, s["pool"], 1)


def test_mapping_revision_vs_submission_preserves_original_topic(client, db, settings):
    from akus.catalog import service as catalog
    from akus.catalog.schemas import MappingWrite

    s = setup(client)
    aid, _ = draft(client, s)
    body = submit_body(client, aid)
    faculty_token = digest(client.cookies.get("akus_demo_session"))
    hod_token = actor_token(client, "hod")
    result = parallel(
        client,
        [
            (
                faculty_token,
                lambda conn, actor: service.submit(conn, actor, uuid4(), UUID(aid), body, settings),
            ),
            (
                hod_token,
                lambda conn, actor: catalog.write_mapping(
                    conn,
                    actor,
                    uuid4(),
                    UUID(s["dept"]),
                    UUID(s["course"]),
                    MappingWrite.model_validate(mapping_body(s, 1, topic_id=s["other_topic"])),
                    settings,
                ),
            ),
        ],
    )
    assert result[1] == "OK"
    assert result[0] in {"OK", "PRIMARY_TOPIC_MAPPING_CHANGED"}
    assert_balance(db, s["pool"], 1 if result[0] == "OK" else 0)
    if result[0] == "OK":
        with client.app.state.sessions() as conn:
            from akus.applications import transfers

            transfers.worker_recheck(conn, UUID(aid))
            conn.commit()
        db.expire_all()
        pending = db.scalar(
            select(Reconciliation).where(
                Reconciliation.application_id == UUID(aid), Reconciliation.kind == "TOPIC_MAPPING"
            )
        )
        assert pending.status == "OPEN"
        assert db.get(Submission, UUID(aid)).facts["topic_id"] == s["topic"]
        assert db.get(Allocation, UUID(aid)).pool_id == UUID(s["pool"])


def test_decrease_vs_reservation_never_exceeds_capacity(client, db, settings):
    from akus.catalog.schemas import QuotaWrite
    from akus.quotas.service import write_pool

    s = setup(client, 1)
    aid, _ = draft(client, s)
    body = submit_body(client, aid)
    ft = digest(client.cookies.get("akus_demo_session"))
    ht = actor_token(client, "hod")
    results = parallel(
        client,
        [
            (
                ft,
                lambda conn, actor: service.submit(conn, actor, uuid4(), UUID(aid), body, settings),
            ),
            (
                ht,
                lambda conn, actor: write_pool(
                    conn,
                    actor,
                    uuid4(),
                    UUID(s["dept"]),
                    QuotaWrite.model_validate(
                        SOURCE
                        | {
                            "topic_id": s["topic"],
                            "academic_year_id": s["year"],
                            "maximum": 0,
                            "publish": True,
                            "expected_version": 1,
                        }
                    ),
                ),
            ),
        ],
    )
    assert results in [["OK", "CAP_BELOW_COUNTED_OCCUPANCY"], ["QUOTA_FULL", "OK"]]
    assert_balance(db, s["pool"], 1 if results[0] == "OK" else 0)


def test_two_offerings_transfer_compete_for_last_target_seat(client, db, settings):
    from akus.catalog import service as catalog
    from akus.catalog.schemas import SnapshotAccept

    s = setup(client, 3)
    h = login(client)
    second = s | {"offering": offering(client, h, s["course"], s["data"])}
    for offering_, role in [(s, "faculty"), (second, "drc")]:
        aid, h = draft(client, offering_, role)
        assert submit(client, aid, h).status_code == 200
    dest = target(client, s, 1)
    tasks = []
    for offering_ in [s, second]:
        _, d, body = observe(client, offering_)
        # Separate source-authenticated browser sessions for each concurrent command.
        token = actor_token(client, "admin")
        oid = UUID(d["id"])
        data = SnapshotAccept.model_validate(body)
        tasks.append(
            (
                token,
                lambda conn, actor, oid=oid, data=data: catalog.accept_snapshot(
                    conn, actor, uuid4(), oid, data, settings
                ),
            )
        )
    assert parallel(client, tasks) == ["OK", "OK"]
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 1)
    assert (
        db.scalar(
            select(func.count())
            .select_from(Reconciliation)
            .join(Application, Application.id == Reconciliation.application_id)
            .where(
                Application.course_id == UUID(s["course"]),
                Reconciliation.kind == "QUOTA_TRANSFER",
                Reconciliation.status == "OPEN",
            )
        )
        == 1
    )


def test_withdrawal_vs_transfer_releases_current_pool_exactly_once(client, db, settings):
    from akus.applications.schemas import Withdraw
    from akus.catalog import service as catalog
    from akus.catalog.schemas import SnapshotAccept

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s)
    _, d, body = observe(client, s)
    admin = actor_token(client, "admin")
    faculty = actor_token(client, "faculty")
    results = parallel(
        client,
        [
            (
                admin,
                lambda conn, actor: catalog.accept_snapshot(
                    conn,
                    actor,
                    uuid4(),
                    UUID(d["id"]),
                    SnapshotAccept.model_validate(body),
                    settings,
                ),
            ),
            (
                faculty,
                lambda conn, actor: service.withdraw(
                    conn,
                    actor,
                    uuid4(),
                    UUID(aid),
                    Withdraw.model_validate(
                        SOURCE | {"expected_version": 2, "not_enrolled_declaration": True}
                    ),
                    settings,
                ),
            ),
        ],
    )
    assert results == ["OK", "OK"]
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 0)
    assert db.get(Allocation, UUID(aid)).state == "RELEASED"
    assert (
        db.scalar(
            select(func.count())
            .select_from(Ledger)
            .where(Ledger.application_id == UUID(aid), Ledger.kind == "WITHDRAW_RELEASE")
        )
        == 1
    )


def test_target_decrease_vs_transfer_is_linearizable(client, db, settings):
    from akus.catalog import service as catalog
    from akus.catalog.schemas import QuotaWrite, SnapshotAccept
    from akus.quotas.service import write_pool

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s, 1)
    _, d, body = observe(client, s)
    admin = actor_token(client, "admin")
    hod = actor_token(client, "hod")
    results = parallel(
        client,
        [
            (
                admin,
                lambda conn, actor: catalog.accept_snapshot(
                    conn,
                    actor,
                    uuid4(),
                    UUID(d["id"]),
                    SnapshotAccept.model_validate(body),
                    settings,
                ),
            ),
            (
                hod,
                lambda conn, actor: write_pool(
                    conn,
                    actor,
                    uuid4(),
                    UUID(s["dept"]),
                    QuotaWrite.model_validate(
                        SOURCE
                        | {
                            "topic_id": s["topic"],
                            "academic_year_id": s["next_year"],
                            "maximum": 0,
                            "publish": True,
                            "expected_version": 1,
                        }
                    ),
                ),
            ),
        ],
    )
    assert results[0] == "OK" and results[1] in {"OK", "CAP_BELOW_COUNTED_OCCUPANCY"}
    expected = 0 if results[1] == "OK" else 1
    assert_balance(db, dest, expected)
    assert_balance(db, s["pool"], 1 - expected)


def test_duplicate_source_accept_and_worker_do_not_duplicate_transfer(client, db):
    from akus.applications import transfers

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s)
    h, d, body = observe(client, s)
    key = uuid4()
    for _ in range(2):
        r = post(client, f"/admin/nptel/offerings/{d['id']}/accept", body, h, key)
        assert r.status_code == 200, r.text
    for _ in range(2):
        with client.app.state.sessions() as conn:
            transfers.worker_recheck(conn, UUID(aid))
            conn.commit()
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 1)
    assert (
        db.scalar(
            select(func.count())
            .select_from(Ledger)
            .where(Ledger.application_id == UUID(aid), Ledger.kind == "TRANSFER")
        )
        == 2
    )


def test_closed_retained_seat_is_not_migrated(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    h = login(client)
    changed = s["data"] | {"starts_on": "2026-01-01"}
    r = post(
        client,
        "/admin/nptel/local-fixtures",
        SOURCE
        | {
            "course_id": s["course"],
            "provider_id": s["offering"]["provider_id"],
            "metadata": changed,
        },
        h,
    )
    assert r.status_code == 200, r.text
    d = client.get("/api/v1/nptel/offerings/" + s["offering"]["id"]).json()
    assert (
        post(
            client,
            f"/admin/nptel/offerings/{d['id']}/accept",
            SOURCE | {"snapshot_id": d["observations"][0]["id"], "expected_version": d["version"]},
            h,
        ).status_code
        == 200
    )
    h = login(client, "faculty")
    r = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
        h,
    )
    assert r.status_code == 200, r.text
    dest = target(client, s)
    reschedule(client, s)
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 0)
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == "QUOTA_TRANSFER"
        )
    )
    assert case.reason == "TERMINAL_RETAINED_POLICY_PENDING"


def test_application_commands_reject_csrf_and_overposted_topic(client):
    s = setup(client)
    aid, h = draft(client, s)
    body = submit_body(client, aid).model_dump(mode="json")
    assert (
        post(
            client, f"/applications/{aid}/submit", body, h | {"X-CSRF-Token": "forged"}
        ).status_code
        == 403
    )
    assert (
        post(
            client, f"/applications/{aid}/submit", body, h | {"Origin": "https://evil.invalid"}
        ).status_code
        == 403
    )
    assert (
        post(
            client, f"/applications/{aid}/submit", body | {"topic_id": s["other_topic"]}, h
        ).status_code
        == 422
    )
    assert submit(client, aid, h).status_code == 200
    h = login(client, "drc")
    # Same department DRC is authorized to review the ordinary faculty submission.
    assert client.get("/api/v1/applications/" + aid).status_code == 200
    h = login(client, "acting-hod")
    assert client.get("/api/v1/applications/" + aid).status_code == 403


def test_pool_identity_and_counted_history_cannot_be_rewritten(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE department_topic_quotas SET topic_id=:topic WHERE id=:id"),
            {"topic": s["other_topic"], "id": s["pool"]},
        )
        db.commit()
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(text("UPDATE quota_ledger SET delta=0 WHERE application_id=:id"), {"id": aid})
    db.rollback()
    assert_balance(db, s["pool"], 1)


def test_quota_ledger_as_of_and_faculty_privacy(client, db):
    from datetime import UTC, datetime

    s = setup(client)
    before = datetime.now(UTC).isoformat()
    aid, h = draft(client, s, "drc")
    assert submit(client, aid, h).status_code == 200
    login(client, "faculty")
    own = client.get("/api/v1/quotas/" + s["pool"]).json()
    assert own["occupied"] == 1 and own["allocations"] == [] and own["ledger"] == []
    assert own["reconciliation"]["matches_current"] is True
    login(client, "principal")
    global_ = client.get("/api/v1/quotas/" + s["pool"]).json()
    assert global_["allocations"][0]["application_id"] == aid
    old = client.get("/api/v1/quotas/" + s["pool"], params={"as_of": before}).json()
    assert (
        old["reconciliation"]["ledger_balance"] == 0
        and old["reconciliation"]["matches_current"] is None
    )


@pytest.mark.parametrize(
    "change,code",
    [
        ({"scheduled_exam_on": None}, "VERIFIED_PROVIDER_DATES_REQUIRED"),
        ({"duration_weeks": None}, "VERIFIED_PROVIDER_DATES_REQUIRED"),
        ({"enrollment_ends_on": "2020-01-01"}, "EXTERNAL_DEADLINE_CLOSED"),
    ],
)
def test_unverified_or_expired_source_never_reserves(client, db, change, code):
    s = setup(client)
    h = login(client)
    changed = s | {"offering": offering(client, h, s["course"], s["data"] | change)}
    aid, h = draft(client, changed)
    r = submit(client, aid, h)
    assert r.json()["error"]["code"] == code, r.text
    assert_balance(db, s["pool"], 0)


def test_effective_office_transition_retains_seat_and_creates_pending_case(client, db):
    from datetime import UTC, datetime, timedelta

    from akus.applications import transfers
    from akus.people.models import OfficeAppointment
    from akus.people.seed import fixture_id

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    # Transaction-local future/effective authority probe; no institutional fixture is overwritten.
    with client.app.state.sessions() as conn:
        office = OfficeAppointment(
            id=uuid4(),
            person_id=fixture_id("faculty"),
            department_id=None,
            office="PRINCIPAL",
            valid_from=datetime.now(UTC) - timedelta(minutes=1),
            valid_until=datetime.now(UTC) + timedelta(minutes=1),
            source_reference="LOCAL_TEST_TRANSITION",
            reason="Synthetic effective office transition in rolled-back transaction",
            version=1,
        )
        # Principal fixture already exists; an overlapping institutional principal is denied.
        # Use an otherwise unoccupied departmental HoD seat to test applicant exemption instead.
        office.original_until = office.valid_until
        office.office = "HOD"
        from akus.people.models import Department

        new_dept = Department(
            id=uuid4(), code="T" + uuid4().hex[:8], name="Synthetic transition department"
        )
        conn.add(new_dept)
        conn.flush()
        office.department_id = new_dept.id
        conn.add(office)
        conn.flush()
        transfers.worker_recheck(conn, UUID(aid))
        pending = conn.scalar(
            select(Reconciliation).where(
                Reconciliation.application_id == UUID(aid),
                Reconciliation.kind == "SOURCE_TRANSITION",
            )
        )
        assert pending.reason == "APPLICANT_SOURCE_CHANGE_POLICY_PENDING"
        assert conn.get(Allocation, UUID(aid)).pool_id == UUID(s["pool"])
        conn.rollback()
    assert_balance(db, s["pool"], 1)


def verify_personal(client, aid, day="2027-07-15", version=0, **overrides):
    from datetime import UTC, datetime, timedelta
    from hashlib import sha256

    h = login(client, "hod")
    return post(
        client,
        f"/applications/{aid}/verify-schedule",
        SOURCE
        | {
            "scheduled_exam_on": day,
            "expected_version": version,
            "document_digest": sha256(b"LOCAL_TEST synthetic official hall ticket").hexdigest(),
            "observed_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            "authenticated_official_person_and_offering": True,
        }
        | overrides,
        h,
    )


def test_personal_hall_ticket_dates_straddle_year_for_same_offering(client, db):
    from akus.applications.models import PersonalSchedule

    s = setup(client, 3)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    bid, h = draft(client, s, "drc")
    assert submit(client, bid, h).status_code == 200
    dest = target(client, s, 3)
    result = verify_personal(client, aid)
    assert result.status_code == 200, result.text
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 1)
    result = verify_personal(client, bid, "2027-06-25")
    assert result.status_code == 200, result.text
    reschedule(client, s, "2027-08-01")
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 1)
    assert db.get(Allocation, UUID(aid)).pool_id == UUID(dest)
    assert db.get(Allocation, UUID(bid)).pool_id == UUID(s["pool"])
    first = db.scalar(select(PersonalSchedule).where(PersonalSchedule.application_id == UUID(aid)))
    assert first.office_id is not None
    with pytest.raises(DBAPIError):
        db.execute(
            text("UPDATE personal_schedule_revisions SET reason='forged' WHERE id=:id"),
            {"id": first.id},
        )
    db.rollback()
    # Current pointers cannot accidentally apply one person's evidence to another.
    with pytest.raises(DBAPIError):
        db.execute(
            text(
                "UPDATE personal_schedule_current SET revision_id=:revision WHERE application_id=:app"
            ),
            {"revision": first.id, "app": bid},
        )
    db.rollback()
    assert db.get(Submission, UUID(aid)).original_pool_id == UUID(s["pool"])


def test_unverified_personal_claim_cannot_move_or_apply_to_other_person(client, db):
    s = setup(client, 3)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    assert (
        post(
            client,
            f"/applications/{aid}/schedule-claims",
            SOURCE | {"scheduled_exam_on": "2027-07-15"},
            h,
        ).status_code
        == 200
    )
    bid, h = draft(client, s, "drc")
    assert submit(client, bid, h).status_code == 200
    dest = target(client, s, 3)
    reschedule(client, s)
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 1)
    case = db.scalar(
        select(Reconciliation).where(
            Reconciliation.application_id == UUID(aid), Reconciliation.kind == "PERSON_SCHEDULE"
        )
    )
    assert case.status == "OPEN"
    assert verify_personal(client, aid).status_code == 200
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 2)
    db.refresh(case)
    assert case.status == "RESOLVED"


@pytest.mark.parametrize("role", ["faculty", "drc", "admin", "principal", "acting-hod"])
def test_personal_schedule_requires_current_distinct_department_hod(client, role):
    from datetime import UTC, datetime

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    h = login(client, role)
    r = post(
        client,
        f"/applications/{aid}/verify-schedule",
        SOURCE
        | {
            "expected_version": 0,
            "scheduled_exam_on": "2027-07-15",
            "document_digest": "a" * 64,
            "observed_at": datetime.now(UTC).isoformat(),
            "authenticated_official_person_and_offering": True,
        },
        h,
    )
    assert r.status_code == 403, r.text


def test_personal_schedule_full_target_stale_revision_and_retry(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s, 0)
    r = verify_personal(client, aid)
    assert r.status_code == 200, r.text
    assert_balance(db, s["pool"], 1)
    assert_balance(db, dest, 0)
    assert verify_personal(client, aid).json()["error"]["code"] == "VERSION_CONFLICT"
    assert (
        verify_personal(client, aid, version=1, observed_at="2020-01-01T00:00:00Z").json()["error"][
            "code"
        ]
        == "STALE_PERSON_SCHEDULE_EVIDENCE"
    )
    assert (
        verify_personal(
            client, aid, version=1, authenticated_official_person_and_offering=False
        ).status_code
        == 422
    )
    h = login(client, "hod")
    assert (
        post(
            client,
            f"/departments/{s['dept']}/quotas",
            SOURCE
            | {
                "topic_id": s["topic"],
                "academic_year_id": s["next_year"],
                "maximum": 1,
                "publish": True,
                "expected_version": 1,
            },
            h,
        ).status_code
        == 200
    )
    assert post(client, f"/applications/{aid}/reconcile", SOURCE, h).status_code == 200
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 1)
    assert db.get(Allocation, UUID(aid)).personal_schedule_id is not None


def test_new_conflicting_provider_observation_blocks_old_snapshot_admission(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    h, d, _ = observe(client, s)
    assert d["source_status"] == "SOURCE_CONFLICT_REVIEW_REQUIRED"
    old = post(
        client,
        f"/admin/nptel/offerings/{d['id']}/accept",
        SOURCE | {"expected_version": d["version"], "snapshot_id": s["offering"]["snapshot_id"]},
        h,
    )
    assert old.status_code == 409 and old.json()["error"]["code"] == "STALE_PROVIDER_EVENT"
    h = login(client, "faculty")
    r = submit(client, aid, h)
    assert (
        r.status_code == 409 and r.json()["error"]["code"] == "SOURCE_MISSING_STALE_OR_UNAVAILABLE"
    )
    assert_balance(db, s["pool"], 0)


def test_withdrawal_before_pending_schedule_acceptance_releases_source_once(client, db):
    """Force the withdrawal-first ordering of the concurrent transfer regression."""
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    dest = target(client, s)
    _, observed, acceptance = observe(client, s)
    assert observed["source_status"] == "SOURCE_CONFLICT_REVIEW_REQUIRED"
    h = login(client, "faculty")
    body = SOURCE | {"expected_version": 2, "not_enrolled_declaration": True}
    key = uuid4()
    first = post(client, f"/applications/{aid}/withdraw", body, h, key)
    assert first.status_code == 200, first.text
    assert post(client, f"/applications/{aid}/withdraw", body, h, key).json() == first.json()
    h = login(client, "admin")
    accepted = post(client, f"/admin/nptel/offerings/{observed['id']}/accept", acceptance, h)
    assert accepted.status_code == 200, accepted.text
    assert_balance(db, s["pool"], 0)
    assert_balance(db, dest, 0)
    movements = list(db.scalars(select(Ledger).where(Ledger.application_id == UUID(aid))))
    assert [entry.kind for entry in movements].count("WITHDRAW_RELEASE") == 1
    assert not any(entry.kind == "TRANSFER" for entry in movements)
    assert db.get(Allocation, UUID(aid)).pool_id == UUID(s["pool"])


def test_conflicting_commencement_blocks_withdrawal_until_verified(client, db):
    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    h = login(client, "admin")
    observed = post(
        client,
        "/admin/nptel/local-fixtures",
        SOURCE
        | {
            "course_id": s["course"],
            "provider_id": s["offering"]["provider_id"],
            "metadata": s["data"] | {"starts_on": "2026-01-01"},
        },
        h,
    )
    assert observed.status_code == 200, observed.text
    h = login(client, "faculty")
    response = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": 2, "not_enrolled_declaration": True},
        h,
    )
    assert response.status_code == 423
    assert response.json()["error"]["code"] == "VERIFIED_COMMENCEMENT_REQUIRED"
    assert_balance(db, s["pool"], 1)


def test_withdrawal_closes_pending_schedule_work_without_verifying_claim(client, db):
    from akus.applications.models import AcademicNotice, PersonalSchedule

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    claim = post(
        client,
        f"/applications/{aid}/schedule-claims",
        SOURCE | {"scheduled_exam_on": "2027-07-15"},
        h,
    )
    assert claim.status_code == 200, claim.text
    reschedule(client, s)
    h = login(client, "faculty")
    current = client.get(f"/api/v1/applications/{aid}").json()
    assert {c["kind"] for c in current["cases"] if c["status"] == "OPEN"} == {
        "QUOTA_TRANSFER",
        "PERSON_SCHEDULE",
    }
    withdrawn = post(
        client,
        f"/applications/{aid}/withdraw",
        SOURCE | {"expected_version": current["version"], "not_enrolled_declaration": True},
        h,
    )
    assert withdrawn.status_code == 200, withdrawn.text
    cases = list(
        db.scalars(select(Reconciliation).where(Reconciliation.application_id == UUID(aid)))
    )
    assert all(
        c.status == "RESOLVED" and c.reason == "APPLICATION_RELEASED_NO_EVIDENCE_OR_POLICY_DECISION"
        for c in cases
    )
    assert (
        db.scalar(select(PersonalSchedule).where(PersonalSchedule.application_id == UUID(aid)))
        is None
    )
    assert db.scalar(
        select(AcademicNotice).where(
            AcademicNotice.application_id == UUID(aid), AcademicNotice.kind == "PERSON_SCHEDULE"
        )
    )
    assert_balance(db, s["pool"], 0)


def test_publishing_capacity_wakes_only_matching_transfer_waiters(client, db):
    from akus.models import WorkJob
    from akus.worker import tick

    left, right = setup(client), setup(client)
    waiting = []
    for fixture in (left, right):
        aid, headers = draft(client, fixture)
        assert submit(client, aid, headers).status_code == 200
        reschedule(client, fixture)
        waiting.append(aid)
    before = set(db.scalars(select(WorkJob.id)))
    new_pool = target(client, left)
    jobs = [job for job in db.scalars(select(WorkJob)) if job.id not in before]
    assert len(jobs) == 1 and jobs[0].key.split(":")[1] == waiting[0]
    with client.app.state.sessions() as work:
        assert tick(work, jobs[0].id)
        assert not tick(work, jobs[0].id)
    assert_balance(db, left["pool"], 0)
    assert_balance(db, new_pool, 1)
    assert_balance(db, right["pool"], 1)


def test_first_publication_vs_cross_year_revision_cannot_lose_wakeup(client, db, settings):
    from akus.catalog import service as catalog
    from akus.catalog.schemas import QuotaWrite, SnapshotAccept
    from akus.models import WorkJob
    from akus.quotas import service as quota
    from akus.worker import tick

    s = setup(client)
    aid, h = draft(client, s)
    assert submit(client, aid, h).status_code == 200
    _, off, accept = observe(client, s)
    publish = QuotaWrite.model_validate(
        SOURCE
        | {
            "topic_id": s["topic"],
            "academic_year_id": s["next_year"],
            "maximum": 1,
            "publish": True,
        }
    )
    result = parallel(
        client,
        [
            (
                actor_token(client, "admin"),
                lambda c, a: catalog.accept_snapshot(
                    c, a, uuid4(), UUID(off["id"]), SnapshotAccept.model_validate(accept), settings
                ),
            ),
            (
                actor_token(client, "hod"),
                lambda c, a: quota.write_pool(c, a, uuid4(), UUID(s["dept"]), publish),
            ),
        ],
    )
    assert result == ["OK", "OK"]
    for jid in db.scalars(
        select(WorkJob.id).where(
            WorkJob.key.like("recheck:" + aid + ":%"), WorkJob.state == "PENDING"
        )
    ):
        with client.app.state.sessions() as worker:
            tick(worker, jid)
    dest = db.scalar(
        select(QuotaPool.id).where(
            QuotaPool.department_id == UUID(s["dept"]),
            QuotaPool.topic_id == UUID(s["topic"]),
            QuotaPool.academic_year_id == UUID(s["next_year"]),
        )
    )
    assert_balance(db, s["pool"], 0)
    assert_balance(db, str(dest), 1)
