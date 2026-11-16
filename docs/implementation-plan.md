# AKUS implementation plan

Binding source: spec/AKUS_MASTER_SPEC.txt. Execution order: codex/BUILD_PHASES.md (its nine phases organize the embedded baseline recommendations). Read spec-inventory.md, POLICY_REGISTER.md, ../POLICY_GAPS.md and ../BUILD_PROGRESS.md on resume. Never change source specs to reconcile contradictions.

## Architecture and boundaries

React 19 strict TypeScript + Vite + React Router + TanStack Query. Radix Dialog provides accessible navigation primitives; local design tokens implement the blueprint. Same-origin /api/v1; generated OpenAPI types. FastAPI/Python 3.13, synchronous SQLAlchemy/Psycopg, PostgreSQL 16, Alembic. Caddy fronts web/API in Compose. No Redis, Kafka, distributed services or remote calls within transactions.

Modules: identity/access; institutional people/employment/offices; academic reference; provider catalog and snapshots; department course-topic mapping; annual topic quotas; applications and reviews; participation/evidence; integrity and separation; independent annual and Silver assessments; audit/reporting; durable work ledger. Each owns its mutations. Command services coordinate one PostgreSQL transaction and immutable audit/outbox. Controllers validate DTOs and call services.

Phase 1 schema is intentionally limited: fictional demo identities, hashed opaque sessions, official-shaped academic-year fixtures, immutable audit, work jobs and worker heartbeat. Fixture roles are not institutional appointments. Phase 2A now adds source-shaped people, employment and effective office authority, exercised with explicitly fictional records. Institutional OIDC remains a separate unfinished Phase 2 slice. No academic mutation API is exposed by Phase 1.

## Work order and acceptance gates

| Phase | Schema / service / UI work | Gate |
|---|---|---|
| 0 | Complete source inventory, 80 routes, 50 policies, all pending rules | Contiguous read manifest, exact embedded-blueprint match, immutable source hashes |
| 1 | PostgreSQL migration, demo sessions, health/readiness, worker, React shell/profile/help, Compose/dev scripts | Real DB migration, seed idempotence, backend tests, lint/typecheck, frontend tests/build, responsive browser proof |
| 2 | People, episodes, offices, institutional Google OIDC, ABAC, five real dashboards | Overlap races; expired grants, self/cross-department access denied; no Principal blanket writes |
| 3 | Canonical courses/offerings, provider snapshots, HoD primary topic revisions and annual quotas | Missing mapping/quota gate, no alternate-category selection, cap race tests |
| 4 | Drafts, atomic submit, route plans, DRC/HoD decisions and withdrawal | Last-seat and canonical duplicate concurrency, retry idempotence, immutable history |
| 5 | Verified reschedules, two-pool transfer, exception cases | Both-pool atomicity, retain+flag failure, repeated/stale events and release races |
| 6 | Evidence, outcomes, annual and Silver ledgers | Actual-exam-year credit, no-repeat, no automatic multi-subject credit, integrity holds |
| 7 | Separation/rehire, historical reassessment | Q41–50, date-only ambiguity, exactly-once current-pool release, immutable as-of |
| 8 | Remaining dedicated pages, reports, ops and security | Complete 80-route/action audit, accessibility, E2E, backup/restore and deployment proof |

Every slice includes migrations, real actions, server authorization, meaningful tests and recorded manual demo before proceeding. Phase 1 does not count the 80 inventory rows as built pages. Production remains fail-closed until OIDC and real authority are implemented. External integrations require verified contracts and approved configuration; no fabricated provider truth.

## Phase 2 execution slices — current session

The next unfinished phase was Phase 2. This session implements **2A: staff source records and effective office authority**. The entire Phase 2 remains IN PROGRESS.

1. Schema: permanent people, departments, non-overlapping employment episodes and home assignments, office intervals, separately provisioned Admin grants, idempotency receipts. Migration 0002 adds schema and immutable issued-office protection; 0003 narrows a duplicate-office restriction without deleting data. Current head: `0003_office_scope`.
2. Server: `akus/access.py` resolves current source authority for every authenticated API request. `people/service.py` owns Admin source transactions, locks people in stable UUID order, rechecks authority, writes audit and command receipt atomically. PostgreSQL enforces global DRC/HoD exclusion even without the service. Principal has global read visibility; HoD reads its current office departments; Faculty/DRC read themselves.
3. API/UI: staff search/detail and history, Admin create-staff page, office register/create/detail/end pages, own source profile. Shared read API `/people/*`; Admin commands `/admin/*`. All commands require current Admin grant, same origin, CSRF, source/reason and UUID idempotency key. Ending also requires version and leaves original source facts immutable. Read aliases are not a permission bypass.
4. Gate: real PG exclusion and duplicate-command races; current/scheduled/expired grants; scope and write denials; idempotence, audit and original-fact preservation; strict code/build checks; Chromium actions, reloads, errors, responsive axe and screenshots; Compose upgrade/browser proof. Observed results belong in TEST_RESULTS.md.

Relevant source reread before edits: master 1095–1189 (ADM page contracts), 1401–1415 (binding A amendments), 1635–1673 (roles/invariants), 1807–1830 (source model), 1901–1925 (authority), 2172–2183 (API/security). Complete master read from Phase 0 remains in spec-inventory.md. Blueprint is duplicate source, not a separate rule hierarchy.

Next **2B: institutional identity and controlled account linking**: Google issuer+subject identity, state/nonce/PKCE callback verification, approved provisioning, person-backed sessions, revocation, provider failure/denial tests and usable linking/denial pages. No fake provider success. Local protocol tests can use a clearly test-only issuer; real institutional credentials/domain/account actions need explicit authorization. Production remains disabled until secure configuration and integration verification exist.

Subsequent Phase 2 work: complete staff department/episode correction and rehire source workflows (respecting unresolved authority and chronology), teaching source pages and five actual source-aware dashboards. Separation/compliance consequences stay in their planned phases. Do not start Phase 3 until the whole Phase 2 gate is met. Phase 2A does not claim any academic approval, quota, provider verification, compliance waiver or full page-contract completion.
