# Build progress

2026-11-16. **Phase 0 complete. Phase 1 runnable foundation implemented and locally verified.** The complete AKUS application is NOT finished. Next implementation phase is **Phase 2 — People and access**, only when requested.

## Source audit

Repository initially contained only starter instructions/specs. Read every master line 1–2607 in bounded sections; separate 1,353-line blueprint verified verbatim embedded. See docs/spec-inventory.md for read coverage and hash. All source specs and instructions remain unchanged. Inventoried 80 route contracts, 50 historical policies and all 27 open/resolved register entries. Explicitly corrected stale Q07 reschedule wording and Q43 original-pool release in the reconciliation register without editing source.

## Files and working behavior

- `apps/api/akus`: FastAPI modules for config, PostgreSQL sessions/models, typed contracts, demo sessions, policy summaries, seed and worker. Six fictional people cover all five role labels plus distinct acting HoD; two July–June demo years. No institutional office/approval authority claimed.
- `apps/api/migrations`: initial forward-only Alembic migration; constraints, restrict-delete FKs and immutable audit triggers. DB-backed login/logout and local worker audit. Hashed opaque sessions with expiry, rotation, CSRF and origin checks. Production fails closed.
- `apps/web/src`: React 19 strict TypeScript shell, role-directed foundation homes, own profile, searchable policy guide and recovery pages, light design tokens, responsive accessible navigation, generated OpenAPI types and real query states. Google is explicitly not configured; NPTEL is not connected.
- `scripts`, `infra`, `compose.yaml`: native DB/dev/check commands and same-origin Caddy/Compose alternative; exact dependency locks and CI definition.
- Persistent documents: implementation-plan, traceability, route-matrix/JSON, reconciled POLICY_REGISTER, POLICY_TEST_TRACEABILITY, POLICY_GAPS, architecture/ADR/DB/security/runbooks/manual and actual test/screenshot evidence.

Working demo: http://127.0.0.1:5173 → choose Mira Rao → enter local workspace → inspect connected services/reference years → Profile & access → Policy guide → search P-51 → reload → sign out. API docs: http://127.0.0.1:8000/api/docs. Native development services and isolated local PostgreSQL are left running for review. The separately built Compose stack is also running at http://127.0.0.1:8080 with compiled frontend, Caddy, API, worker and fresh migrated PostgreSQL.

## Verification

`TEST_RESULTS.md` and `docs/qa/*` contain observed commands/output. Final native gate: **21 backend tests, 2 UI tests, 12 browser tests passed**; Ruff/mypy/ESLint/TypeScript/Prettier/build, migrations and drift check pass. The same 12 browser tests also pass against the compiled Compose stack (9.9s). Responsive axe checks pass at 1440/1024/768/390/320; real screenshots saved. Fixed initial mobile scroll-region keyboard accessibility failure. Four-worker database claim test proves local probe idempotence only, not quota concurrency.

## Limits and next slice

The 80 routes are inventoried, not fully built. Demo profile/help and role homes are explicit Phase 1 subsets. Google OAuth callback is an honest not-configured boundary. No application, quota, approval, certificate/compliance, personnel-office administration or provider-validation workflows are exposed. No real secrets, external accounts or cloud deployment were touched. Production, remote CI and backup/restore are unverified/unavailable. All policy gaps remain pending; confirmed V2.3/V2.4 rules are not misclassified as gaps.

Phase 2 must add real roster/person records, employment episodes, effective-dated department/office appointments with global DRC/HoD non-overlap, Google OIDC/session integration, current server-authoritative permissions, five actual role dashboards and denial/revocation/concurrency tests. Demo role labels must never become authority for academic operations. Do not start Phase 3 before Phase 2 gate is complete.

Resume instructions: read AGENTS.md, docs/codex/BUILD_PHASES.md, docs/implementation-plan.md, docs/traceability.md, docs/POLICY_REGISTER.md, POLICY_GAPS.md and TEST_RESULTS.md; inspect code and run documented checks. Continue from the next unfinished phase rather than recreating scaffolding. Preserve all spec/audit/scan evidence and unresolved decisions.
