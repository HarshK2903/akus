# Build progress

2026-11-16. **Phase 0 complete; Phase 1 verified; Phase 2 IN PROGRESS.** Implemented and locally verified the next complete vertical slice: **2A — staff source records and effective office authority**. The complete AKUS application and the whole Phase 2 are NOT finished. Prior Phase 1 progress is preserved in `docs/qa/phase1-build-progress.md`.

## Current working slice

- PostgreSQL migrations `0002_people_access` and `0003_office_scope`: permanent people, departments, non-overlapping episodes/home assignments, effective offices, separate Admin grants, command receipts. Global DRC/HoD/acting-HoD exclusion applies across departments and competing DB writers. Original issued-office facts cannot be rewritten/deleted; end operations preserve original expiry.
- `apps/api/akus/access.py`: source-derived current authority on every authenticated request. Demo role labels cannot grant access. Faculty/DRC applicant eligibility retained; HoD/acting/Principal exempt. Principal reads globally; HoD reads current office departments; Faculty/DRC read self. Source writes require an explicit current Admin grant.
- `apps/api/akus/people/{models,schemas,router,service,seed}.py`: scoped APIs and real create-staff/create-office/end-office commands. Lock/recheck authority, origin/CSRF, source/reason, UUID idempotency receipts, optimistic version and immutable audit in the same transaction. Office end immediately removes source authority from existing sessions. API returns safe conflict/pending errors.
- `apps/web/src/pages/StaffDirectory.tsx`, `StaffNew.tsx`, `StaffRecord.tsx`, `Appointments.tsx`, `AppointmentNew.tsx`, `AppointmentRecord.tsx`: light responsive pages with real forms, source histories, deep links/reloads, read-only variants, conflict feedback, pagination, confirmation and cache refresh. Ending is a full-page action, not modal-only. Own profile displays source employment/offices and current access. Admin/Principal/HoD homes link to real scoped pages but remain partial dashboards.
- Reproducible native/Compose runtime retained. Fixed native dev child-process cleanup so restarting does not orphan Vite. Seeded rehire and separated people have stable identities and no login; all data is conspicuously fictional. Creating a person does not create a Google account or grant an office.

## Verification and running review

Full local gate passes: **45 PostgreSQL backend tests, 2 UI tests**, Ruff/format/mypy, ESLint/TypeScript, migration upgrade/drift check and production build. Browser evidence: **20 passed on native and 20 on compiled Compose**; detailed and focused checks are recorded in TEST_RESULTS.md. Source forms/registers have zero reported axe violations at 1440/390/320; foundation retains 1440/1024/768/390/320 checks. Browser sessions verify creation/end/history, conflict retention, read-only/scoped access and source authority changing without signing in again. Desktop and mobile screenshots were visually inspected.

All migrations also passed from an empty isolated `akus_phase2a_fresh_test` database, followed by no schema drift and two successful seeds. Compose upgraded its existing Phase 1 database without volume removal; migrate exited 0 and API/database are healthy. No existing audit records, source specs or scan reports were deleted.

Open **http://127.0.0.1:8080** (compiled Compose) or **http://127.0.0.1:5173** (native). API docs: http://127.0.0.1:8000/api/docs. Both stacks and isolated databases are left running for review.

Demo: select **Nila Shah · Admin → Staff directory → Add staff record**; save identity/employment with a LOCAL/DEMO source; open detail → Record appointment; choose an unoccupied office interval; view appointment → enter end reason/source and confirm → End appointment now. Reopen staff history to inspect recorded changes. **Arun Sen + acting HoD in another department** is rejected. **Dev Mehta · Principal** sees the global source register without write controls. Full instructions: `docs/USER_MANUAL.md`.

## Scope boundaries and next unfinished work

**Next: Phase 2B — institutional Google OIDC and controlled account linking**, before Phase 3. Implement issuer+subject identity, verified provisioning, callback state/nonce/PKCE/signature/issuer/audience/expiry checks, person-backed sessions and denial/revocation/linking pages with protocol tests. Real domain/credentials/account actions require explicit authorization; no fake provider success. Production remains fail-closed.

Also unfinished in Phase 2: employment/department correction and rehire commands, teaching source management, full role dashboards and complete ADM/SHR contracts. Office changes currently create/end source authority only. Arbitrary backdated correction and scheduled cancellation are not exposed. Active-case/obligation consequences of HoD transitions remain POLICY_PENDING (P-NEW-05/06); no academic case tables exist yet. Add controlled impact cases before enabling academic intake. No applications, quota, review, certificate verification, annual/Silver assessment or institutional provider integrations are implemented. No cloud deployment or external account action occurred. Runtime DB least-privilege hardening, backup/restore, real OIDC and remote CI remain unverified.

## Persistent resume instructions

Read AGENTS.md, docs/codex/BUILD_PHASES.md, this file, docs/implementation-plan.md, docs/traceability.md, docs/POLICY_REGISTER.md, POLICY_GAPS.md and TEST_RESULTS.md, then relevant master sections before edits. Phase 0 read all 2,607 master lines, verified the embedded blueprint, inventoried 80 route contracts, reconciled all 50 historical policies and 27 register entries. Those specs/hashes remain unchanged. This session reread source/authority/page/security sections documented in implementation-plan.md. Traceability explicitly distinguishes executable source prerequisites from unfinished academic policy tests; do not mark all 80 routes or Phase 2 complete. Continue from 2B, not scaffolding recreation.
