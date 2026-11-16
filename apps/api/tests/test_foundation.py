from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from akus.auth import digest
from akus.config import Settings
from akus.db import database
from akus.main import COOKIE, create_app
from akus.models import AcademicYear, AuditEvent, AuthSession, DemoIdentity, WorkJob
from akus.seed import seed
from akus.worker import tick

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def login(client: TestClient, identity: str = "faculty") -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/demo-login", json={"identity_key": identity}, headers=ORIGIN
    )
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    return response.json()  # type: ignore[no-any-return]


def test_live_ready_openapi(client: TestClient) -> None:
    assert client.get("/api/v1/health/live").json()["status"] == "alive"
    assert client.get("/api/v1/health/ready").json()["database"] == "connected"
    schema = client.get("/api/openapi.json").json()
    assert "/api/v1/me" in schema["paths"]
    assert not any("submit" in path or "approve" in path for path in schema["paths"])


def test_unavailable_database_not_green() -> None:
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://unavailable@127.0.0.1:1/missing", _env_file=None
        )
    )
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").status_code == 200
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert "password" not in response.text and "Traceback" not in response.text
    app.state.engine.dispose()


@pytest.mark.parametrize("endpoint", ["/me", "/foundation", "/academic-years", "/policy/help"])
def test_reads_require_session(client: TestClient, endpoint: str) -> None:
    response = client.get("/api/v1" + endpoint)
    assert response.status_code == 401
    assert response.json()["error"]["correlation_id"] == response.headers["x-request-id"]


@pytest.mark.parametrize(
    "identity,role",
    [
        ("faculty", "FACULTY"),
        ("drc", "DRC_HEAD"),
        ("hod", "HOD"),
        ("principal", "PRINCIPAL"),
        ("admin", "ADMIN"),
        ("acting-hod", "HOD"),
    ],
)
def test_demo_identity_is_server_resolved(client: TestClient, identity: str, role: str) -> None:
    login(client, identity)
    result = client.get("/api/v1/me", headers={"X-Role": "PRINCIPAL"}).json()
    assert result["role"] == role and result["mode"] == "LOCAL_DEMO"
    assert len(client.get("/api/v1/academic-years").json()) == 2


def test_forged_fields_origin_and_identity_denied(client: TestClient) -> None:
    assert (
        client.post(
            "/api/v1/auth/demo-login",
            json={"identity_key": "faculty", "role": "HOD"},
            headers=ORIGIN,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/auth/demo-login",
            json={"identity_key": "faculty"},
            headers={"Origin": "https://evil.invalid"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/auth/demo-login", json={"identity_key": "unknown"}, headers=ORIGIN
        ).status_code
        == 401
    )


def test_logout_csrf_and_revocation(client: TestClient, db: Session) -> None:
    result = login(client)
    token = client.cookies.get(COOKIE)
    assert db.get(AuthSession, digest(str(token))) is not None
    assert client.post("/api/v1/auth/logout", headers=ORIGIN).status_code == 403
    assert client.get("/api/v1/me").status_code == 200
    assert (
        client.post(
            "/api/v1/auth/logout", headers=ORIGIN | {"X-CSRF-Token": str(result["csrf_token"])}
        ).status_code
        == 204
    )
    assert client.get("/api/v1/me", headers={"Cookie": f"{COOKIE}={token}"}).status_code == 401


def test_login_rotates_session_and_expiry_is_enforced(client: TestClient, db: Session) -> None:
    login(client)
    old = client.cookies.get(COOKIE)
    login(client, "drc")
    assert db.get(AuthSession, digest(str(old))) is None
    current = db.get(AuthSession, digest(str(client.cookies.get(COOKIE))))
    assert current is not None
    current.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/v1/me").status_code == 401


def test_demo_disabled_and_production_fail_closed(settings: Settings) -> None:
    with TestClient(create_app(settings.model_copy(update={"demo_enabled": False}))) as client:
        assert client.get("/api/v1/auth/demo-identities").status_code == 404
        assert (
            client.post(
                "/api/v1/auth/demo-login", json={"identity_key": "faculty"}, headers=ORIGIN
            ).status_code
            == 404
        )
    with pytest.raises(ValidationError):
        Settings(env="production", demo_enabled=True, _env_file=None)
    with pytest.raises(ValidationError):
        Settings(env="production", demo_enabled=False, _env_file=None)
    with pytest.raises(ValidationError):
        Settings(demo_enabled=True, public_origin="https://public.invalid", _env_file=None)


def test_seed_idempotent_and_year_constraints(db: Session) -> None:
    seed(db)
    seed(db)
    assert db.scalar(select(func.count()).select_from(DemoIdentity)) == 6
    assert db.scalar(select(func.count()).select_from(AcademicYear)) == 2
    db.add(AcademicYear(label="invalid", starts_on=date(2030, 1, 1), ends_on=date(2030, 12, 31)))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize(
    "operation",
    [
        "UPDATE audit_events SET action='forged' WHERE id=:id",
        "DELETE FROM audit_events WHERE id=:id",
    ],
)
def test_audit_database_immutability(db: Session, operation: str) -> None:
    event = AuditEvent(action="TEST_IMMUTABILITY", details={})
    db.add(event)
    db.commit()
    with pytest.raises(DBAPIError):
        db.execute(text(operation), {"id": event.id})
        db.commit()
    db.rollback()
    assert db.get(AuditEvent, event.id).action == "TEST_IMMUTABILITY"  # type: ignore[union-attr]


def test_pending_rules_not_confirmed(client: TestClient) -> None:
    login(client)
    rules = {r["id"]: r for r in client.get("/api/v1/policy/help").json()}
    for code in ["P-51", "P-NEW-11", "P-NEW-04", "P-NEW-05/06", "P-NEW-10"]:
        assert rules[code]["status"] == "POLICY_PENDING"
    assert rules["V2.4"]["status"] == "CONFIRMED"
    assert rules["V2.3"]["status"] == "CONFIRMED"


def test_worker_claim_once_under_concurrency(settings: Settings, db: Session) -> None:
    engine, factory = database(settings.database_url)
    # Settle earlier demo probe jobs; no data deletion or audit rewriting.
    while True:
        with factory() as worker_db:
            if not tick(worker_db):
                break
    job = WorkJob(key=f"race-{uuid4()}", kind="LOCAL_DEMO_BOOTSTRAP", state="PENDING")
    db.add(job)
    db.commit()
    barrier = Barrier(4)

    def run() -> bool:
        barrier.wait()
        with factory() as worker_db:
            return tick(worker_db)

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(lambda _: run(), range(4))) == 1
    db.expire_all()
    assert db.get(WorkJob, job.id).state == "DONE"  # type: ignore[union-attr]
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.details["job_id"].astext == str(job.id))
        )
        == 1
    )
    engine.dispose()
