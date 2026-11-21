from datetime import UTC, datetime, timedelta
from hmac import new as hmac_new
from secrets import token_urlsafe
from typing import Any
from uuid import UUID

from sqlalchemy import delete, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import authority
from akus.auth import digest
from akus.config import Settings
from akus.identity.models import (
    AccountRequest,
    ExternalIdentity,
    InstitutionalEmail,
    InstitutionalSession,
    VerifiedEmailObservation,
)
from akus.identity.provider import ISSUER
from akus.models import AuditEvent
from akus.people.models import Person


def security_event(db: Session, action: str, **details: str) -> None:
    db.add(AuditEvent(action=action, details=details))


def serialize_links(db: Session) -> None:
    # A global, short-lived account-link lock gives deterministic duplicate checks
    # across email imports, reconcile commands and simultaneous first callbacks.
    db.execute(text("SELECT pg_advisory_xact_lock(8210402)"))


def email_candidates(db: Session, email: str) -> list[UUID]:
    now = datetime.now(UTC)
    return list(
        db.scalars(
            select(InstitutionalEmail.person_id)
            .where(
                InstitutionalEmail.normalized_email == email.lower(),
                InstitutionalEmail.valid_from <= now,
                or_(InstitutionalEmail.valid_until.is_(None), InstitutionalEmail.valid_until > now),
            )
            .distinct()
        )
    )


def eligible_person(db: Session, person_id: UUID) -> Person:
    person = db.scalar(select(Person).where(Person.id == person_id).with_for_update())
    if person is None or not person.enabled:
        raise HTTPException(403, "ACCOUNT_DISABLED")
    # Resolve the same live authority used on every API request before issuing a session.
    dummy = InstitutionalSession(person_id=person.id)
    authority(db, None, dummy)
    if person.demo_identity_id is not None:
        raise HTTPException(403, "DEMO_PERSON_CANNOT_LINK")
    return person


def account_link(db: Session, claims: dict[str, Any]) -> tuple[ExternalIdentity | None, str]:
    serialize_links(db)
    db.expire_all()
    subject, email = str(claims["sub"]), str(claims["email"])
    link = db.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.issuer == ISSUER, ExternalIdentity.subject == subject
        )
    )
    if link:
        if link.revoked_at:
            return None, "account-disabled"
        try:
            eligible_person(db, link.person_id)
        except HTTPException:
            return None, "account-disabled"
        db.execute(
            insert(VerifiedEmailObservation)
            .values(external_identity_id=link.id, email=email)
            .on_conflict_do_nothing(constraint="verified_email_observation_once")
        )
        # A changed email never moves an immutable subject to another person.
        return link, "linked"
    request = db.scalar(
        select(AccountRequest).where(
            AccountRequest.issuer == ISSUER, AccountRequest.subject == subject
        )
    )
    if request and request.status == "DENIED":
        return None, "account-not-authorized"
    candidates = email_candidates(db, email)
    status = "account-pending"
    if len(candidates) == 1:
        try:
            person = eligible_person(db, candidates[0])
        except HTTPException:
            return None, "account-disabled"
        existing = db.scalar(
            select(ExternalIdentity.id).where(
                ExternalIdentity.person_id == person.id, ExternalIdentity.revoked_at.is_(None)
            )
        )
        if existing:
            status = "duplicate-link"
        else:
            link = ExternalIdentity(
                person_id=person.id, issuer=ISSUER, subject=subject, linked_email=email
            )
            db.add(link)
            db.flush()
            db.execute(
                insert(VerifiedEmailObservation)
                .values(external_identity_id=link.id, email=email)
                .on_conflict_do_nothing(constraint="verified_email_observation_once")
            )
            if request:
                request.status, request.person_id = "LINKED", person.id
            security_event(
                db, "GOOGLE_IDENTITY_LINKED", person_id=str(person.id), identity_id=str(link.id)
            )
            return link, "linked"
    elif len(candidates) > 1:
        status = "duplicate-link"
    db.execute(
        insert(AccountRequest)
        .values(issuer=ISSUER, subject=subject, email=email, status="PENDING")
        .on_conflict_do_nothing(constraint="one_account_request")
    )
    security_event(db, "GOOGLE_LINK_PENDING", outcome=status)
    return None, status


def csrf_for(token: str, settings: Settings) -> str:
    return hmac_new(
        settings.session_key.get_secret_value().encode(), token.encode(), "sha256"
    ).hexdigest()


def issue_session(
    db: Session, link: ExternalIdentity, settings: Settings, old_token: str | None
) -> str:
    if old_token:
        db.execute(
            delete(InstitutionalSession).where(InstitutionalSession.token_hash == digest(old_token))
        )
    episode = authority(db, None, InstitutionalSession(person_id=link.person_id)).episode
    token = token_urlsafe(32)
    db.add(
        InstitutionalSession(
            token_hash=digest(token),
            person_id=link.person_id,
            external_identity_id=link.id,
            episode_id=episode.id,
            csrf_hash=digest(csrf_for(token, settings)),
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    security_event(db, "GOOGLE_LOGIN", person_id=str(link.person_id), identity_id=str(link.id))
    return token
