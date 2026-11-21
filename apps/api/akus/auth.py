from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from akus.identity.models import InstitutionalSession
from akus.models import AuditEvent, AuthSession, DemoIdentity
from akus.people.models import Person


def digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def resolve(db: Session, token: str | None) -> tuple[AuthSession, DemoIdentity] | None:
    if not token:
        return None
    session = db.get(AuthSession, digest(token))
    if session is None or session.expires_at <= datetime.now(UTC):
        return None
    identity = db.get(DemoIdentity, session.identity_id)
    return (session, identity) if identity else None


def sign_in(db: Session, key: str, old_token: str | None) -> tuple[DemoIdentity, str, str] | None:
    identity = db.scalar(select(DemoIdentity).where(DemoIdentity.key == key))
    if identity is None:
        return None
    if old_token:
        old = db.get(AuthSession, digest(old_token))
        if old:
            db.delete(old)
    from akus.access import current_episode

    person_id = db.scalar(select(Person.id).where(Person.demo_identity_id == identity.id))
    episode = (
        current_episode(db, person_id, datetime.now(ZoneInfo("Asia/Kolkata")).date())
        if person_id
        else None
    )
    token, csrf = token_urlsafe(32), token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=digest(token),
            identity_id=identity.id,
            episode_id=episode.id if episode else None,
            csrf_hash=digest(csrf),
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    db.add(
        AuditEvent(actor_id=identity.id, action="LOCAL_DEMO_LOGIN", details={"mode": "LOCAL_DEMO"})
    )
    db.commit()
    return identity, token, csrf


def csrf_valid(session: AuthSession | InstitutionalSession, value: str) -> bool:
    return compare_digest(session.csrf_hash, digest(value))
