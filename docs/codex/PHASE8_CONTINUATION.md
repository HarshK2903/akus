# AKUS — PHASE 8 EXECUTION AND ACCEPTANCE HANDOFF

## Mission

Act as the Principal Software Engineer, Security Engineer, Senior Frontend Engineer, Database Architect, and QA Lead for the **existing** AKUS repository. Implement and verify the next **approved Phase 8** according to the repository's actual `AGENTS.md`, `docs/codex/BUILD_PHASES.md`, latest master specification, UI/UX blueprint, requirements traceability, and progress/checklist documents. This is a continuation: **do not create a second application, restart completed phases, or invent unratified institutional decisions**.

Begin execution now. Do not stop at planning. Continue in complete, testable slices and leave durable progress after each slice in case Codex usage limits interrupt work.

## Last reported checkpoint — verify against the repository

The previous run reported that Phase 7 passed its **local** acceptance criteria:

- 272 PostgreSQL backend tests passed (four dependency deprecation warnings).
- 2 frontend unit tests passed.
- 42 standard Playwright journeys and 4 isolated browser journeys passed, including mobile/accessibility checks.
- Ruff, mypy, ESLint, TypeScript, formatting and production builds passed; Vite reported a bundle-size advisory.
- Existing Docker build/startup succeeded; frontend HTTP 200, API ready, PostgreSQL connected and worker heartbeat current.
- Migration head `0019_employment_sessions` on the **original** PostgreSQL Docker volume, with no reported schema drift.
- All 18 quota, compliance, employment and audit discrepancy counters were zero across four databases.
- Staff employment-episode end/rejoin workflows, historical as-of reporting and authorization-sensitive staff visibility were implemented.
- Local AKUS was reported reachable at `http://127.0.0.1:8080`.

These are **previous-session claims, not automatic proof of the current state**. Inspect current files, runtime and logs; preserve the existing checkpoint.

## 1. Read, recover and classify before changing code

1. Read `AGENTS.md`, `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/BUILD_PHASES.md`, latest AKUS master specification, UI/UX blueprint, institutional policy amendments, and requirements traceability.
2. Find the actual Phase 8 acceptance checklist, if present. If absent, **derive a scoped checklist from the approved build plan**, labeling its provenance; do not silently expand or replace the project plan.
3. Review current `git status --short --branch`, `git diff`, newly created/untracked files, migration head, Docker Compose services, and existing QA artifacts. **Never wipe or reset uncommitted work**.
4. Reconcile the original 80-route inventory (or whatever the currently authoritative inventory says), role-permission matrix, backend endpoint inventory, and the actual functioning browser routes. Differentiate implemented/live, stub, blocked-by-policy, and planned-later routes.
5. Produce a concise Phase 8 issue/acceptance matrix ordered by impact, then **start resolving the highest-impact unfinished approved slice**.
6. Use only the repository's approved Phase 8 scope. If it includes final UI/UX completion, security and QA, follow the detailed instructions below; if the approved scope differs, adapt to the actual files and record the distinction.

## 2. Preserve all institutional decisions and security constraints

Latest overriding role policy:

- Faculty: subject to NPTEL and eligible to apply; ordinary route is Faculty → DRC Head → HoD.
- DRC Head: is faculty, has NPTEL obligations, and their own application goes directly to HoD.
- HoD and Principal: exempt from compulsory NPTEL personal application/obligations.
- DRC Head and HoD must be different people even with effective-dated or acting appointments; enforce in backend and database.
- Principal: institution-wide oversight/visibility, not blanket mutation or personal participation.
- Admin: administrative records/appointments, not automatic academic decision authority.

Latest governing quota system:

- Shared HoD-published quota keyed `(department, approved canonical charging topic, July–June academic year)`; NOT the superseded per-offering quota.
- HoD approves one primary topic per `(department, canonical NPTEL course)` while effective; faculty may not quota-shop among provider categories.
- Initial quota year is based on official scheduled exam date available at valid submission; actual verified exam date controls final annual compliance.
- Valid submission atomically reserves one seat; publication, idempotency, concurrency and audit rules hold.
- Verified cross-year exam reschedule attempts atomic capacity-checked migration. When destination missing, unpublished or full, retain original counted allocation and create a reconciliation case.
- Quota changes may not invalidate counted occupancy; closure, withdrawal, integrity invalidation and separation follow distinct approved rules; never double release.

Historic Q01–Q50 policies remain binding where consistent with later overrides. Critically, **DO NOT invent** resolution for unratified policies (including IO-02 teaching-allocation acceptance, Q-51 multi-subject Silver reuse, retroactive topic-mapping revision effects on existing reservations, blocked transfer final disposition, or general evidence-review authorities). Create explicit policy-pending UI states and a traceable policy gap register where needed. Do not bypass these gates with convenience defaults.

## 3. Complete the actual approved Phase 8 user journeys and page quality

Where Phase 8 includes end-to-end UI/UX completion:

- Follow the project's professionally restrained **light-theme enterprise design**, spacious multi-page navigation, coherent sidebars/breadcrumbs, readable tables, forms, details and task flows. Avoid an all-in-one dashboard, fake interactions, or decorative-only controls.
- Audit every role's navigation: Faculty, DRC Head, HoD, Principal, Admin; ensure actions only appear when permitted and server-side authorization remains authoritative.
- Match the route inventory exactly. For each route, establish what loads, real data source, authorized actions, navigation to next page, loading/empty/error/success states and acceptance tests.
- Finish approved workflows for staff onboarding/Excel-CSV imports, source corrections, offices, teaching assignments, NPTEL catalogs/provider provenance, HoD topic mappings/quotas, academic application/review, enrollment, prior attempts, integrity, cross-year transfer, departure/rehire, verified certificates, annual compliance and Silver obligations where within Phase 8 or needed for complete cross-page journeys.
- Keep prior/closed applications, effective-dated evidence and audit/history read-only where required. Use real backend API responses; do not hardcode fake live counts or success toasts.
- Correct mobile/tablet breakpoints, keyboard navigation, visible focus, landmarks, labels, ARIA where warranted, contrast, clear errors and accessible dialogs. Test complex forms and long data tables.
- Preserve meaningful URL/deep links, query-driven filters, pagination, user context and filter persistence. Prevent stale permission or status actions after navigation.
- Ensure UI never obscures a policy-pending or external-verification state by treating it as verified success.

## 4. Backend, API, data and operational hardening

Where approved by the Phase 8 plan:

- Verify authorization on **every** protected read/write endpoint, organizational scoping, current effective-dated offices, deny-by-default behavior and non-self-approval.
- Verify CSRF/origin safeguards, server sessions, Google OIDC callback validation, approved staff identity linking, and secrets handling. Do not introduce local-login shortcuts into institutional mode.
- Audit file upload types/sizes, evidence integrity, content serving/download authorization, storage path safety, security headers, PII exposure/logging, pagination and error handling.
- Revalidate PostgreSQL transaction boundaries, deterministic lock order, exactly-once reservation/transfer/release, idempotency and append-only audits. Test last-seat and concurrent policy transitions.
- Verify historical as-of and latest-assessment reporting are both reproducible, especially after post-separation certificates and late HR corrections.
- Investigate and address applicable dependency deprecations and the Vite bundle-size advisory without destabilizing the system. Record any remaining non-blocking advisories rather than disguising them.
- Maintain health/readiness checks, worker monitoring, migrations, QA artifacts and restart-safe operational behavior.
- Verify integration contracts with real NPTEL provider information, but do not claim live certificate authenticity verification or malware scanning without actually testing/configuring those external capabilities.

## 5. Google and external acceptance boundaries

Real institutional Google OIDC sign-in is **not yet verified**. An appropriate approved OAuth client, institutional staff/appointments and voluntary user participation are required. The intended acceptance-test accounts are:

- Faculty: `faculty-harsh1.cse24@cmrit.ac.in`
- HoD: `hod-ankit.cse24@cmrit.ac.in`
- DRC Head: `DRC-awanish.cse24@cmrit.ac.in`
- Admin: `admin-harsh.cse24@cmrit.ac.in`
- Principal: `principle-nikshay.cse24@cmrit.ac.in`

Do not treat these addresses as proof of identity or authorization. Do not assign permissions by email prefix, request passwords, fabricate user logins, or embed OAuth secrets. Keep live Google testing as an external **acceptance gate**, and proceed with independent Phase 8 implementation. If authorized credentials are present, provide exact human-assisted login steps and verify the claims only with the account holder's consent.

## 6. Existing Docker and Postgres: preserve, don't reset

- Reuse existing Docker Compose services and current PostgreSQL named volume. Inspect service names before using any command.
- NEVER use `docker compose down -v`, `docker volume prune`, dropping/resetting the institutional database, deleting migrations or overwriting real data without explicit user permission.
- Use safe migrations and non-destructive acceptance databases for tests. Preserve existing data and evidence.
- Do not decide production hosting/infrastructure on the user's behalf.
- If a tool command requires permission, request normal approval rather than bypassing restrictions; distinguish tool-denied from test-failed.

## 7. Test-driven verification and explicit acceptance evidence

Implement each approved slice with matching backend models/services/routers, migrations, frontend behavior and tests. After each slice, run focused tests; then run full final gate:

1. PostgreSQL-backed backend suite and migration upgrade checks on a safe database.
2. Frontend unit tests; TypeScript, ESLint, Prettier, Ruff and mypy.
3. Vite production build; verify asset/layout behavior and note bundle advisories.
4. Playwright standard and isolated journeys with desktop/mobile and accessibility checks.
5. Permission-denial and cross-role security tests, including DRC/HoD mutual exclusion and inactive employment.
6. Capacity/concurrency/transfer/closure integrity tests and live **read-only** reconciliation checks.
7. Docker build/healthy startup and frontend/API/worker health.
8. Route-inventory and requirements traceability coverage, with each unfinished item distinctly marked.

Do not weaken, delete or skip tests just to produce a passing summary. If a check fails, investigate root cause and rerun. Treat exit codes as authoritative—do not mistake an intermediate 'All checks passed' line for the command's final result.

## 8. Durable checkpointing and truthful final report

At the end of **every completed vertical slice**, update these existing files (or repository equivalents):

- `BUILD_PROGRESS.md` (what changed, route/workflow coverage, remaining slices)
- `TEST_RESULTS.md` (actual commands, exit statuses, counts and QA log paths)
- Phase 8 checklist / acceptance matrix
- Requirements traceability / policy pending register
- Relevant setup, security and user documentation

Preserve log and evidence paths and leave a short **NEXT ACTION** checkpoint for a new Codex session. Avoid long low-value prose or repeated audits when a concrete coding task is ready.

Final report must distinguish: (a) code implemented, (b) locally verified acceptance, (c) externally blocked/unverified integration, (d) unratified institutional policies, (e) production-readiness gaps. Do not claim full institutional or production readiness while real Google OIDC acceptance, live provider certificate verification, malware scanning, and policy decisions remain outstanding.

## Execution command

**Start now: inspect the repository and actual Phase 8 plan; verify Phase 7 checkpoint and preserve everything; implement approved Phase 8 functionality immediately in tested slices; fix failures; rerun the final gate; update progress files and report accurate results. Do not stop at planning.**
