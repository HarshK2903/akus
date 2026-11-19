import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from akus.access import DB, Current, authority
from akus.applications.outcome_router import router as outcomes_router
from akus.applications.router import router as applications_router
from akus.auth import csrf_valid, resolve, sign_in
from akus.body_limit import BodyLimitMiddleware
from akus.catalog.router import router as catalog_router
from akus.config import Settings
from akus.db import database
from akus.exceptions.router import router as exceptions_router
from akus.identity.router import router as identity_router
from akus.models import AcademicYear, AuditEvent, DemoIdentity, WorkerHeartbeat
from akus.people.router import router as people_router
from akus.policy import HELP
from akus.schemas import (
    AuthConfig,
    DemoLogin,
    Foundation,
    Health,
    Identity,
    LoginResult,
    PolicyHelp,
    Year,
)
from akus.sources.router import router as sources_router

log = logging.getLogger("akus")
if not log.handlers:
    log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)
log.propagate = False
COOKIE = "akus_demo_session"
SCHEMA_HEAD = "0016_archived_obligations"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, factory = database(settings.database_url)
    app = FastAPI(
        title="AKUS NPTEL API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(BodyLimitMiddleware)
    app.state.engine = engine
    app.state.sessions = factory
    app.state.settings = settings
    app.include_router(people_router)
    app.include_router(identity_router)
    app.include_router(sources_router)
    app.include_router(catalog_router)
    app.include_router(applications_router)
    app.include_router(outcomes_router)
    app.include_router(exceptions_router)

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.correlation_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        log.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method,
                    "status": response.status_code,
                    "correlation_id": request.state.correlation_id,
                }
            )
        )
        return response

    def error(request: Request, status: int, code: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": code.replace("_", " ").capitalize(),
                    "correlation_id": request.state.correlation_id,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error(request, exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error(request, 422, "INVALID_REQUEST")

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return error(request, 503, "DATABASE_UNAVAILABLE")

    def demo_only() -> None:
        if not settings.demo_enabled:
            raise HTTPException(404, "NOT_FOUND")

    def origin(request: Request) -> None:
        if request.headers.get("origin") != settings.public_origin:
            raise HTTPException(403, "ORIGIN_REJECTED")

    @app.get("/api/v1/health/live", response_model=Health)
    def live() -> Health:
        return Health(status="alive")

    @app.get("/api/v1/health", response_model=Health)
    @app.get("/api/v1/health/ready", response_model=Health)
    def ready(db: DB, response: Response) -> Health:
        try:
            revision = db.scalar(text("SELECT version_num FROM alembic_version"))
            db.execute(select(AcademicYear.id).limit(1))
            if revision != SCHEMA_HEAD:
                response.status_code = 503
                return Health(status="not_ready", database="connected", schema_version="mismatch")
        except SQLAlchemyError:
            response.status_code = 503
            return Health(status="not_ready", database="unavailable")
        return Health(status="ready", database="connected", schema_version=SCHEMA_HEAD)

    @app.get("/api/v1/auth/config", response_model=AuthConfig)
    def auth_config() -> AuthConfig:
        return AuthConfig(
            demo_enabled=settings.demo_enabled,
            google_enabled=settings.google_enabled,
            institution_label=settings.institution_label,
        )

    @app.get("/api/v1/auth/demo-identities", response_model=list[Identity])
    def identities(db: DB) -> list[Identity]:
        demo_only()
        return [
            Identity.model_validate(i)
            for i in db.scalars(select(DemoIdentity).order_by(DemoIdentity.key))
        ]

    @app.post("/api/v1/auth/demo-login", response_model=LoginResult)
    def demo_login(body: DemoLogin, request: Request, response: Response, db: DB) -> LoginResult:
        demo_only()
        origin(request)
        result = sign_in(db, body.identity_key, request.cookies.get(COOKIE))
        if result is None:
            raise HTTPException(401, "DEMO_IDENTITY_NOT_FOUND")
        identity, token, csrf = result
        response.set_cookie(
            COOKIE,
            token,
            httponly=True,
            secure=False,
            samesite="strict",
            max_age=28800,
            path="/api",
        )
        authenticated = resolve(db, token)
        assert authenticated is not None
        try:
            view = authority(db, identity, authenticated[0]).view()
        except HTTPException:
            db.delete(authenticated[0])
            db.commit()
            raise
        return LoginResult(identity=view, csrf_token=csrf)

    @app.get("/api/v1/me", response_model=Identity)
    def me(auth: Current) -> Identity:
        return auth.view()

    @app.post("/api/v1/auth/logout", status_code=204)
    def logout(request: Request, response: Response, db: DB, auth: Current) -> None:
        origin(request)
        if not csrf_valid(auth.session, request.headers.get("x-csrf-token", "")):
            raise HTTPException(403, "CSRF_REJECTED")
        db.delete(auth.session)
        db.add(
            AuditEvent(
                actor_id=auth.demo.id if auth.demo else None,
                action="LOCAL_DEMO_LOGOUT" if auth.demo else "GOOGLE_LOGOUT",
                details={"person_id": str(auth.person.id)},
            )
        )
        db.commit()
        response.delete_cookie(COOKIE, path="/api")
        response.delete_cookie("akus_session", path="/api")

    @app.get("/api/v1/academic-years", response_model=list[Year])
    def academic_years(db: DB, auth: Current) -> list[Year]:
        return [
            Year.model_validate(y)
            for y in db.scalars(select(AcademicYear).order_by(AcademicYear.starts_on))
        ]

    @app.get("/api/v1/foundation", response_model=Foundation)
    def foundation(db: DB, auth: Current) -> Foundation:
        heartbeat = db.get(WorkerHeartbeat, "foundation")
        now = datetime.now(UTC)
        healthy = heartbeat is not None and heartbeat.seen_at > now - timedelta(seconds=30)
        return Foundation(
            worker="running" if healthy else "not_reporting",
            google="configured" if settings.google_enabled else "not_configured",
            worker_seen_at=heartbeat.seen_at if heartbeat else None,
            institution_label=settings.institution_label,
            checked_at=now,
        )

    @app.get("/api/v1/policy/help", response_model=list[PolicyHelp])
    def policy_help(auth: Current) -> list[PolicyHelp]:
        return HELP

    return app
