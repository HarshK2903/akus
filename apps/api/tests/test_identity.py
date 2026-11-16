from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from akus.auth import digest
from akus.config import Settings
from akus.identity.models import (
    ExternalIdentity,
    InstitutionalEmail,
    InstitutionalSession,
    OidcFlow,
)
from akus.identity.operator import BootstrapRoster, bootstrap
from akus.identity.provider import ISSUER, GoogleProvider, validate_token
from akus.identity.service import account_link
from akus.main import create_app
from akus.people.models import DepartmentAssignment, EmploymentEpisode, Person
from akus.people.seed import fixture_id


@pytest.fixture
def signing_key():
    return RSAKey.generate_key(2048, parameters={"kid": "isolated-test-key"})


def claims(**overrides):
    now = datetime.now(UTC).timestamp()
    return {
        "iss": ISSUER,
        "sub": str(uuid4()),
        "aud": "isolated-client",
        "exp": now + 300,
        "iat": now,
        "nonce": "test-nonce",
        "email": "test@example.test",
        "email_verified": True,
        "hd": "cmrit.ac.in",
    } | overrides


def signed(signing_key, values):
    return jwt.encode({"alg": "RS256", "kid": "isolated-test-key"}, values, signing_key)


def verify(signing_key, values):
    return validate_token(
        signed(signing_key, values),
        {"keys": [signing_key.as_dict(private=False)]},
        "isolated-client",
        "test-nonce",
    )


@pytest.mark.parametrize(
    "patch",
    [
        {"iss": "https://attacker.invalid"},
        {"aud": "other-client"},
        {"hd": "other.ac.in"},
        {"email_verified": False},
        {"email_verified": "true"},
        {"nonce": "wrong"},
        {"exp": 1},
        {"iat": 9999999999},
        {"azp": "other-client"},
        {"email": "outside@gmail.com"},
        {"aud": ["isolated-client", "another"], "azp": "another"},
    ],
)
def test_oidc_rejects_invalid_claims(signing_key, patch):
    with pytest.raises((JoseError, ValueError)):
        verify(
            signing_key,
            claims(email="fictional@cmrit.ac.in", **patch)
            if "email" not in patch
            else claims(**patch),
        )


@pytest.mark.parametrize("missing", ["sub", "nonce", "hd", "email", "exp", "iat", "aud", "iss"])
def test_oidc_requires_security_claims(signing_key, missing):
    values = claims(email="fictional@cmrit.ac.in")
    del values[missing]
    with pytest.raises((JoseError, ValueError)):
        verify(signing_key, values)


def test_oidc_signature_and_good_verified_claims(signing_key):
    values = claims(email="fictional@cmrit.ac.in")
    assert verify(signing_key, values)["iss"] == ISSUER
    other = RSAKey.generate_key(2048, parameters={"kid": "isolated-test-key"})
    with pytest.raises((JoseError, ValueError)):
        validate_token(
            signed(other, values),
            {"keys": [signing_key.as_dict(private=False)]},
            "isolated-client",
            "test-nonce",
        )


def provision(db: Session, email: str | None = None, *, enabled=True, separated=False):
    person = Person(
        staff_key=f"OIDC-{uuid4().hex[:20]}",
        display_name="Fictional security test",
        enabled=enabled,
        source_reference="ISOLATED_TEST_ONLY",
    )
    db.add(person)
    db.flush()
    episode = EmploymentEpisode(
        person_id=person.id,
        starts_on=datetime(2020, 7, 1).date(),
        ends_before=datetime(2022, 7, 1).date() if separated else None,
        is_faculty=True,
        source_reference="ISOLATED_TEST_ONLY",
    )
    db.add(episode)
    db.flush()
    db.add(
        DepartmentAssignment(
            episode_id=episode.id,
            department_id=fixture_id("CSE"),
            starts_on=episode.starts_on,
            ends_before=episode.ends_before,
            source_reference="ISOLATED_TEST_ONLY",
        )
    )
    email = email or f"fictional-{uuid4().hex}@cmrit.ac.in"
    db.add(
        InstitutionalEmail(
            person_id=person.id,
            email=email,
            normalized_email=email.lower(),
            valid_from=datetime(2020, 7, 1, tzinfo=UTC),
            source_reference="ISOLATED_TEST_ONLY",
        )
    )
    db.commit()
    return person, email


@pytest.fixture
def oidc(settings, monkeypatch, signing_key):
    cfg = Settings(
        env="test",
        demo_enabled=False,
        database_url=settings.database_url,
        public_origin="http://127.0.0.1:5173",
        google_client_id="isolated-client",
        google_client_secret="ISOLATED_TEST_NOT_A_CREDENTIAL",
        session_key=Fernet.generate_key().decode(),
        google_redirect_uri="http://127.0.0.1:5173/api/v1/auth/google/callback",
        _env_file=None,
    )
    monkeypatch.setattr(
        GoogleProvider,
        "metadata",
        lambda _: {"authorization_endpoint": ISSUER + "/o/oauth2/v2/auth"},
    )

    def exchange(self, code, nonce, verifier):
        assert len(verifier) >= 43
        return validate_token(
            code, {"keys": [signing_key.as_dict(private=False)]}, cfg.google_client_id, nonce
        )

    monkeypatch.setattr(GoogleProvider, "exchange", exchange)
    app = create_app(cfg)
    with TestClient(app, follow_redirects=False) as client:
        yield client
    app.state.engine.dispose()


def login(oidc, signing_key, email, subject=None):
    response = oidc.get("/api/v1/auth/google/begin?return_to=/app/profile")
    assert response.status_code == 303
    params = parse_qs(urlsplit(response.headers["location"]).query)
    assert params["code_challenge_method"] == ["S256"]
    assert set(params["scope"][0].split()) == {"openid", "email", "profile"}
    values = claims(email=email, nonce=params["nonce"][0], **({"sub": subject} if subject else {}))
    callback = oidc.get(
        "/api/v1/auth/google/callback",
        params={"state": params["state"][0], "code": signed(signing_key, values)},
    )
    return callback, params


def test_oidc_real_signature_callback_session_csrf_logout(db, oidc, signing_key):
    person, email = provision(db)
    response, params = login(oidc, signing_key, email)
    assert response.headers["location"] == "/app/profile"
    assert (
        "HttpOnly" in response.headers["set-cookie"]
        and "SameSite=lax" in response.headers["set-cookie"]
    )
    result = oidc.get("/api/v1/auth/session").json()
    assert result["identity"]["person_id"] == str(person.id)
    assert result["identity"]["mode"] == "INSTITUTIONAL"
    assert oidc.get("/api/v1/auth/demo-identities").status_code == 404
    assert (
        oidc.post("/api/v1/auth/logout", headers={"Origin": "http://127.0.0.1:5173"}).status_code
        == 403
    )
    repeated = oidc.get(
        "/api/v1/auth/google/callback", params={"state": params["state"][0], "code": "replayed"}
    )
    assert repeated.headers["location"] == "/auth/sign-in-failed"
    assert (
        oidc.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": result["csrf_token"]},
        ).status_code
        == 204
    )
    assert oidc.get("/api/v1/me").status_code == 401


@pytest.mark.parametrize("state_mode", ["wrong", "expired", "wrong_browser", "consent", "nonce"])
def test_oidc_callback_failures(db, oidc, signing_key, state_mode):
    response = oidc.get("/api/v1/auth/google/begin")
    params = parse_qs(urlsplit(response.headers["location"]).query)
    state = params["state"][0]
    if state_mode == "wrong":
        state = "not-the-state"
    if state_mode == "wrong_browser":
        oidc.cookies.clear()
    if state_mode == "expired":
        flow = db.get(OidcFlow, digest(state))
        flow.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    callback = oidc.get(
        "/api/v1/auth/google/callback",
        params={
            "state": state,
            "code": signed(signing_key, claims(email="fictional@cmrit.ac.in", nonce="wrong")),
            **({"error": "access_denied"} if state_mode == "consent" else {}),
        },
    )
    assert callback.headers["location"].startswith("/auth/")
    assert oidc.get("/api/v1/me").status_code == 401


def test_oidc_session_rotation_expiry_and_live_separation(db, oidc, signing_key):
    person, email = provision(db)
    subject = str(uuid4())
    login(oidc, signing_key, email, subject)
    old = oidc.cookies.get("akus_session")
    login(oidc, signing_key, email, subject)
    current = oidc.cookies.get("akus_session")
    assert old != current
    assert db.get(InstitutionalSession, digest(old)) is None
    session = db.get(InstitutionalSession, digest(current))
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert oidc.get("/api/v1/me").status_code == 401
    login(oidc, signing_key, email, subject)
    episode = db.scalar(select(EmploymentEpisode).where(EmploymentEpisode.person_id == person.id))
    episode.ends_before = datetime.now(UTC).date()
    db.commit()
    assert oidc.get("/api/v1/me").status_code == 403
    assert oidc.get("/api/v1/me").status_code == 401


@pytest.mark.parametrize(
    "case,expected",
    [
        ("unapproved", "account-pending"),
        ("disabled", "account-disabled"),
        ("separated", "account-disabled"),
        ("duplicate_email", "duplicate-link"),
        ("new_subject", "duplicate-link"),
    ],
)
def test_linking_denials(db, case, expected):
    email = f"fictional-{uuid4().hex}@cmrit.ac.in"
    if case != "unapproved":
        provision(db, email, enabled=case != "disabled", separated=case == "separated")
    if case == "duplicate_email":
        provision(db, email)
    if case == "new_subject":
        assert account_link(db, claims(email=email))[0]
        db.commit()
    link, outcome = account_link(db, claims(email=email))
    assert link is None and outcome == expected
    db.commit()


def test_subject_does_not_move_when_email_changes(db):
    person, email = provision(db)
    subject = str(uuid4())
    first, _ = account_link(db, claims(email=email, sub=subject))
    db.commit()
    other, other_email = provision(db)
    second, _ = account_link(db, claims(email=other_email, sub=subject))
    assert second.id == first.id and second.person_id == person.id != other.id
    db.commit()


def test_two_subjects_racing_to_link_one_person(db, client):
    person, email = provision(db)
    barrier = Barrier(8)

    def contender(_):
        with client.app.state.sessions() as session:
            barrier.wait(timeout=10)
            link, status = account_link(session, claims(email=email))
            session.commit()
            return status

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(contender, range(8)))
    assert results.count("linked") == 1
    assert results.count("duplicate-link") == 7
    assert (
        db.scalar(
            select(func.count())
            .select_from(ExternalIdentity)
            .where(ExternalIdentity.person_id == person.id)
        )
        == 1
    )


def test_bootstrap_is_operator_only_idempotent_and_no_session(settings, client):
    cfg = Settings(
        env="test", database_url=settings.database_url, demo_enabled=False, _env_file=None
    )
    row = BootstrapRoster(
        staff_key="TEST-FIRST-ADMIN",
        display_name="Synthetic operator fixture",
        email="synthetic-bootstrap@cmrit.ac.in",
        department_code="TESTOPS",
        department_name="Synthetic operations",
        employment_starts_on=datetime(2020, 7, 1).date(),
        authorized_from=datetime(2020, 7, 1, tzinfo=UTC),
        source_reference="ISOLATED_TEST_AUTHORIZATION",
    )
    with client.app.state.engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            assert bootstrap(db, cfg, row) == "PROVISIONED_REQUIRES_GENUINE_GOOGLE_LOGIN"
            assert bootstrap(db, cfg, row) == "ALREADY_PROVISIONED"
            person = db.scalar(select(Person).where(Person.staff_key == row.staff_key))
            assert (
                db.scalar(
                    select(InstitutionalSession).where(InstitutionalSession.person_id == person.id)
                )
                is None
            )
        transaction.rollback()
    assert client.post("/api/v1/auth/bootstrap").status_code == 404


def test_configuration_and_redirect_boundaries(settings, client):
    from akus.identity.router import safe_return

    for value in ["//evil.invalid", "https://evil.invalid", "/app/\\evil", "/app/%2f%2fevil"]:
        assert safe_return(value) == "/auth/complete"
    assert safe_return("/people/teaching?subject=abc") == "/people/teaching?subject=abc"
    assert (
        client.get("/api/v1/auth/google/begin", follow_redirects=False).headers["location"]
        == "/auth/configuration-required"
    )
    with pytest.raises(ValueError):
        Settings(google_client_id="partial-config", _env_file=None)


def test_google_http_exchange_uses_discovery_pkce_and_trusted_jwks(
    monkeypatch, settings, signing_key
):
    import httpx
    from authlib.integrations.httpx_client import OAuth2Client

    from akus.identity.provider import DISCOVERY

    cfg = Settings(
        env="test",
        database_url=settings.database_url,
        demo_enabled=False,
        public_origin="http://127.0.0.1:5173",
        google_client_id="isolated-client",
        google_client_secret="ISOLATED_TEST_NOT_A_CREDENTIAL",
        session_key=Fernet.generate_key().decode(),
        google_redirect_uri="http://127.0.0.1:5173/api/v1/auth/google/callback",
        _env_file=None,
    )
    visited = []
    metadata = {
        "issuer": ISSUER,
        "authorization_endpoint": ISSUER + "/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
    }

    def handler(request):
        visited.append(str(request.url))
        if str(request.url) == DISCOVERY:
            return httpx.Response(200, json=metadata)
        if str(request.url) == metadata["token_endpoint"]:
            payload = parse_qs(request.content.decode())
            assert payload["code_verifier"] == ["v" * 43]
            assert payload["code"] == ["ISOLATED_AUTHORIZATION_CODE"]
            assert payload["grant_type"] == ["authorization_code"]
            return httpx.Response(
                200,
                json={
                    "access_token": "ISOLATED_NOT_A_REAL_TOKEN",
                    "token_type": "Bearer",
                    "id_token": signed(signing_key, claims(email="synthetic@cmrit.ac.in")),
                },
            )
        if str(request.url) == metadata["jwks_uri"]:
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"keys": [signing_key.as_dict(private=False)]})
        raise AssertionError("Unexpected provider endpoint")

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx.HTTPTransport, "handle_request", lambda self, request: handler(request)
    )
    monkeypatch.setattr(
        GoogleProvider,
        "client",
        lambda _: OAuth2Client(
            cfg.google_client_id,
            cfg.google_client_secret.get_secret_value(),
            redirect_uri=cfg.google_redirect_uri,
            transport=transport,
        ),
    )
    result = GoogleProvider(cfg).exchange("ISOLATED_AUTHORIZATION_CODE", "test-nonce", "v" * 43)
    assert result["email"] == "synthetic@cmrit.ac.in"
    assert visited == [DISCOVERY, metadata["token_endpoint"], metadata["jwks_uri"]]


def test_admin_reconciliation_replaces_exact_link_and_revokes_live_session(
    db, client, oidc, signing_key
):
    from test_people import login as demo_login

    from akus.identity.models import AccountRequest

    person, email = provision(db)
    old_subject, new_subject = str(uuid4()), str(uuid4())
    login(oidc, signing_key, email, old_subject)
    old_link = db.scalar(select(ExternalIdentity).where(ExternalIdentity.person_id == person.id))
    _, outcome = account_link(db, claims(email=email, sub=new_subject))
    assert outcome == "duplicate-link"
    db.commit()
    pending = db.scalar(select(AccountRequest).where(AccountRequest.subject == new_subject))
    headers = demo_login(client)
    body = {
        "action": "APPROVE",
        "person_id": str(person.id),
        "reason": "ISOLATED approved identity replacement",
        "source_reference": "ISOLATED_TEST_ORDER",
    }
    endpoint = f"/api/v1/admin/account-requests/{pending.id}/resolve"
    assert client.post(endpoint, json=body, headers=headers).status_code == 409
    result = client.post(
        endpoint, json=body | {"replace_identity_id": str(old_link.id)}, headers=headers
    )
    assert result.status_code == 200, result.text
    assert oidc.get("/api/v1/me").status_code == 401
    db.expire_all()
    assert db.get(ExternalIdentity, old_link.id).revoked_at is not None
    assert account_link(db, claims(email=email, sub=old_subject))[1] == "account-disabled"
    db.rollback()
    assert login(oidc, signing_key, email, new_subject)[0].headers["location"] == "/app/profile"
    assert oidc.get("/api/v1/me").json()["person_id"] == str(person.id)


def test_denied_pending_request_does_not_auto_link_later(db, client):
    from test_people import login as demo_login

    from akus.identity.models import AccountRequest

    email, subject = f"synthetic-{uuid4().hex}@cmrit.ac.in", str(uuid4())
    account_link(db, claims(email=email, sub=subject))
    db.commit()
    pending = db.scalar(select(AccountRequest).where(AccountRequest.subject == subject))
    response = client.post(
        f"/api/v1/admin/account-requests/{pending.id}/resolve",
        headers=demo_login(client),
        json={
            "action": "DENY",
            "reason": "ISOLATED access not authorized",
            "source_reference": "ISOLATED_TEST_ORDER",
        },
    )
    assert response.status_code == 200
    provision(db, email)
    assert account_link(db, claims(email=email, sub=subject))[1] == "account-not-authorized"
    db.rollback()


def test_verified_changed_email_history_is_separate_from_authoritative_roster(db):
    from akus.identity.models import VerifiedEmailObservation

    person, email = provision(db)
    subject = str(uuid4())
    link, _ = account_link(db, claims(sub=subject, email=email))
    db.commit()
    changed = f"changed-{uuid4().hex}@cmrit.ac.in"
    again, _ = account_link(db, claims(sub=subject, email=changed))
    db.commit()
    assert again.person_id == person.id
    observed = list(
        db.scalars(
            select(VerifiedEmailObservation.email).where(
                VerifiedEmailObservation.external_identity_id == link.id
            )
        )
    )
    assert set(observed) == {email, changed}
    assert (
        db.scalar(select(InstitutionalEmail.email).where(InstitutionalEmail.person_id == person.id))
        == email
    )


def test_https_cookies_and_complete_configuration_fail_closed(settings, signing_key, monkeypatch):
    from fastapi.testclient import TestClient

    cfg = Settings(
        env="test",
        database_url=settings.database_url,
        demo_enabled=False,
        public_origin="https://akus.example.test",
        google_client_id="isolated-client",
        google_client_secret="ISOLATED_NOT_A_CREDENTIAL",
        session_key=Fernet.generate_key().decode(),
        google_redirect_uri="https://akus.example.test/api/v1/auth/google/callback",
        _env_file=None,
    )
    monkeypatch.setattr(
        GoogleProvider,
        "authorization_url",
        lambda self, state, nonce, verifier: ISSUER + "/auth?state=" + state,
    )
    app = create_app(cfg)
    with TestClient(app, base_url=cfg.public_origin, follow_redirects=False) as client:
        response = client.get("/api/v1/auth/google/begin")
        assert (
            "Secure" in response.headers["set-cookie"]
            and "HttpOnly" in response.headers["set-cookie"]
        )
    app.state.engine.dispose()
    with pytest.raises(ValueError):
        Settings(
            env="local",
            demo_enabled=True,
            public_origin="http://127.0.0.1:5173",
            google_client_id="isolated",
            google_client_secret="ISOLATED_NOT_A_CREDENTIAL",
            session_key=Fernet.generate_key().decode(),
            google_redirect_uri="http://127.0.0.1:5173/api/v1/auth/google/callback",
            _env_file=None,
        )
