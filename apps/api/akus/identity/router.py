from datetime import UTC, datetime, timedelta
from secrets import compare_digest, token_urlsafe
from typing import Annotated
from uuid import UUID

from cryptography.fernet import Fernet
from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from starlette.exceptions import HTTPException

from akus.access import DB, Current
from akus.auth import digest
from akus.identity import service
from akus.identity.models import AccountRequest, ExternalIdentity, OidcFlow
from akus.identity.provider import GoogleProvider
from akus.people.router import mutation_guard
from akus.people.schemas import CommandResult
from akus.people.service import commit_command, lock_command, replay, require_admin

router = APIRouter(prefix="/api/v1", tags=["Institutional identity"])


def safe_return(path: str) -> str:
    # Only existing protected route prefixes; reject encoded/control/backslash redirects.
    if len(path) > 500 or any(c in path for c in ("\\", "%", "\r", "\n", "#")):
        return "/auth/complete"
    if path.startswith(("/app/", "/drc/", "/hod/", "/principal/", "/admin/", "/people/")):
        return path
    return "/auth/complete"


@router.get("/auth/google/begin")
def begin(
    request: Request, db: DB, return_to: str = Query("/auth/complete", max_length=500)
) -> RedirectResponse:
    cfg = request.app.state.settings
    if not cfg.google_enabled:
        return RedirectResponse("/auth/configuration-required", status_code=303)
    # No open DB transaction while fetching discovery.
    state, browser, nonce, verifier = (token_urlsafe(32) for _ in range(4))
    try:
        url = GoogleProvider(cfg).authorization_url(state, nonce, verifier)
    except Exception:
        return RedirectResponse("/auth/provider-unavailable", status_code=303)
    service.serialize_links(db)
    peer = digest(request.client.host if request.client else "unknown")
    count = (
        db.scalar(
            select(func.count())
            .select_from(OidcFlow)
            .where(
                OidcFlow.peer_hash == peer,
                OidcFlow.created_at > datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        or 0
    )
    if count >= 60:
        raise HTTPException(429, "SIGN_IN_RATE_LIMIT")
    db.add(
        OidcFlow(
            state_hash=digest(state),
            browser_hash=digest(browser),
            peer_hash=peer,
            nonce=nonce,
            encrypted_verifier=Fernet(cfg.session_key.get_secret_value().encode())
            .encrypt(verifier.encode())
            .decode(),
            return_to=safe_return(return_to),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    db.commit()
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(
        "akus_oidc_flow",
        browser,
        max_age=600,
        httponly=True,
        secure=cfg.secure_cookies,
        samesite="lax",
        path="/api/v1/auth/google",
    )
    return response


@router.get("/auth/google/callback")
def callback(
    request: Request,
    db: DB,
    state: str = Query("", max_length=200),
    code: str = Query("", max_length=4096),
    error: str = Query("", max_length=200),
) -> RedirectResponse:
    cfg = request.app.state.settings
    response = RedirectResponse("/auth/sign-in-failed", status_code=303)
    response.delete_cookie("akus_oidc_flow", path="/api/v1/auth/google")
    if not cfg.google_enabled:
        response.headers["location"] = "/auth/configuration-required"
        return response
    flow = db.scalar(select(OidcFlow).where(OidcFlow.state_hash == digest(state)).with_for_update())
    if (
        not flow
        or flow.consumed_at
        or flow.expires_at <= datetime.now(UTC)
        or not compare_digest(flow.browser_hash, digest(request.cookies.get("akus_oidc_flow", "")))
    ):
        db.rollback()
        return response
    nonce, verifier, destination = flow.nonce, flow.encrypted_verifier, flow.return_to
    flow.consumed_at = datetime.now(UTC)
    db.commit()  # Consume once before network exchange. A repeated callback cannot log in.
    if error or not code:
        response.headers["location"] = "/auth/consent-denied"
        return response
    try:
        claims = GoogleProvider(cfg).exchange(
            code,
            nonce,
            Fernet(cfg.session_key.get_secret_value().encode())
            .decrypt(verifier.encode(), ttl=660)
            .decode(),
        )
    except Exception:
        service.security_event(
            db, "GOOGLE_CALLBACK_REJECTED", reason="TOKEN_EXCHANGE_OR_VALIDATION_FAILED"
        )
        db.commit()
        return response
    link, outcome = service.account_link(db, claims)
    if link:
        token = service.issue_session(db, link, cfg, request.cookies.get("akus_session"))
        response.set_cookie(
            "akus_session",
            token,
            max_age=28800,
            httponly=True,
            secure=cfg.secure_cookies,
            samesite="lax",
            path="/api",
        )
        response.headers["location"] = destination
    else:
        response.headers["location"] = f"/auth/{outcome}"
    db.commit()
    return response


@router.get("/auth/session")
def session_details(request: Request, actor: Current) -> dict[str, object]:
    token = request.cookies.get("akus_session", "")
    return {
        "identity": actor.view().model_dump(mode="json"),
        "csrf_token": service.csrf_for(token, request.app.state.settings)
        if not actor.demo
        else None,
    }


@router.get("/admin/account-requests")
def requests(db: DB, actor: Current, offset: int = Query(0, ge=0)) -> dict[str, object]:
    require_admin(actor)
    records = db.scalars(
        select(AccountRequest)
        .order_by(AccountRequest.recorded_at.desc(), AccountRequest.id)
        .offset(offset)
        .limit(50)
    )
    return {
        "items": [
            {
                "id": r.id,
                "email": r.email,
                "status": r.status,
                "reason": r.reason,
                "person_id": r.person_id,
                "recorded_at": r.recorded_at,
            }
            for r in records
        ],
        "total": db.scalar(select(func.count()).select_from(AccountRequest)) or 0,
    }


class Reconcile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(pattern="^(APPROVE|DENY)$")
    person_id: UUID | None = None
    replace_identity_id: UUID | None = None
    reason: str = Field(min_length=10, max_length=1000)
    source_reference: str = Field(min_length=3, max_length=300)


@router.post("/admin/account-requests/{request_id}/resolve", response_model=CommandResult)
def reconcile(
    request_id: UUID,
    body: Reconcile,
    request: Request,
    db: DB,
    actor: Current,
    idempotency_key: Annotated[UUID, Header()],
) -> CommandResult:
    mutation_guard(request, actor)
    service.serialize_links(db)
    actor = lock_command(db, actor, body.person_id)
    operation = f"ACCOUNT_RESOLVE:{request_id}"
    if result := replay(db, actor, idempotency_key, operation, body):
        return result
    record = db.get(AccountRequest, request_id)
    if not record:
        raise HTTPException(404, "NOT_FOUND")
    if record.status != "PENDING":
        raise HTTPException(409, "ACCOUNT_REQUEST_ALREADY_RESOLVED")
    if body.action == "APPROVE":
        if not body.person_id or service.email_candidates(db, record.email) != [body.person_id]:
            raise HTTPException(409, "APPROVED_UNAMBIGUOUS_EMAIL_RECORD_REQUIRED")
        person = service.eligible_person(db, body.person_id)
        existing_subject = db.scalar(
            select(ExternalIdentity.id).where(
                ExternalIdentity.issuer == record.issuer, ExternalIdentity.subject == record.subject
            )
        )
        if existing_subject:
            raise HTTPException(409, "IMMUTABLE_SUBJECT_CANNOT_MOVE")
        old = db.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.person_id == person.id, ExternalIdentity.revoked_at.is_(None)
            )
        )
        if old:
            if old.id != body.replace_identity_id:
                raise HTTPException(409, "EXPLICIT_REPLACEMENT_REQUIRED")
            old.revoked_at = datetime.now(UTC)
            db.flush()
        elif body.replace_identity_id:
            raise HTTPException(409, "REPLACEMENT_NOT_CURRENT")
        link = ExternalIdentity(
            person_id=person.id,
            issuer=record.issuer,
            subject=record.subject,
            linked_email=record.email,
        )
        db.add(link)
        record.person_id = person.id
        record.status = "APPROVED"
    else:
        record.status = "DENIED"
    record.reason = body.reason
    return commit_command(
        db,
        actor,
        idempotency_key,
        operation,
        body,
        record.id,
        {
            "reason": body.reason,
            "source_reference": body.source_reference,
            "person_id": str(body.person_id or ""),
            "resolution": record.status,
        },
    )
