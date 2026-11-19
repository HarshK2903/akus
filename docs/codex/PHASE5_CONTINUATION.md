# AKUS — PHASE 5 CONTINUATION AND IMPLEMENTATION INSTRUCTIONS

## Mission
You are a Principal Software Engineer, Staff Backend Engineer, PostgreSQL Transaction Specialist, and Senior Frontend Engineer continuing an EXISTING AKUS repository. Work from the repository's actual current state. Do not create another project or redo Phases 1–4.

Last visible Codex report (VERIFY, do not assume still true): Phase 4 local acceptance passed: 210 PostgreSQL backend tests, 2 frontend tests, 36 Playwright tests; Ruff, mypy, ESLint, TypeScript, formatting, production builds passed; API + DB + worker healthy; migration head `0012_prior_outcomes`; live quota reconciliation found zero inconsistent pools/invalid transfers; existing Docker volume and data preserved. Application at http://localhost:8080. Phase 2 real institutional Google login acceptance remains pending external approved OAuth client, institutional roster/appointments, and account-holder participation. Next approved phase is Phase 5: rescheduling and exceptional cases.

## 1. Recover checkpoint without destructive operations
1. Read AGENTS.md, BUILD_PROGRESS.md, TEST_RESULTS.md, docs/codex/BUILD_PHASES.md, docs/codex/PHASE4_CHECKLIST.md, available Phase 5 checklist, applicable latest master spec, policy register, and route traceability. If a file is absent, document that and use the existing source of truth; do not invent its contents.
2. Inspect git status, branch, git diff, untracked files, migrations, running Docker Compose services, relevant logs, and recent test reports. Honor in-progress uncommitted work.
3. Confirm Phase 4 is actually complete; remedy a real regression before proceeding. Do not rerun whole phases without reason.
4. Safeguard the existing PostgreSQL data and Docker volumes. NEVER use docker compose down -v, docker volume rm, database drop/reset, or destructive seed operations. Ask before any destructive migration/data repair.
5. Make a concise Phase 5 coverage checklist with implementation status and specification references, then IMPLEMENT rather than stopping at planning.

## 2. Phase 5 scope — repository-approved specification takes precedence
Implement the actual next-phase requirements listed in BUILD_PHASES.md/master specification, with real SQLAlchemy/PostgreSQL transactional services, FastAPI endpoints, authorization, role-scoped React routes and screens, audit, notifications, and tests. Include the following confirmed cross-policy themes where in scope:

### A. NPTEL published schedule revisions
- Maintain provider metadata versions and distinguish published/scheduled exam dates from actual verified exam dates. Course start, exam-registration cutoff, enrollment cutoff, hall-ticket evidence, and original submission snapshot remain traceable.
- Apply confirmed rule: one shared annual quota pool per (department, HoD-approved canonical topic, July–June academic year); successful submission charges the year of the published scheduled exam date at submission.
- On reliably verified NPTEL exam rescheduling across a July–June boundary, attempt one capacity-checked ATOMIC migration of the application's counted seat from its CURRENT pool into the published destination year pool for the same department and approved charging topic.
- Lock both pools in deterministic order, revalidate source allocation/state and destination capacity, write balanced reservation ledger entries, update current charged pool and save immutable revision/audit/outbox in one transaction. Ensure retries and concurrent revisions are idempotent.
- If target pool is absent/unpublished/full, DO NOT migrate, overbook, create a second seat, auto-reject, or silently release. Keep source occupancy counted and create an authorized reconciliation case/notification. Show it on appropriate HoD and oversight pages.
- Multiple reschedules, stale source updates, application closure or withdrawal racing with transfer, and a final exam date differing from projections need tests. Actual verified exam date still controls annual credit under Q35 independently of quota status.
- An HoD course-to-primary-topic mapping revision is separate from cross-YEAR rescheduling; do not automatically migrate old topic reservations while its retroactive policy is UNRATIFIED.

### B. Employment separation exceptional paths (Q41–Q49)
- Official effective dates determine whether an applicant separated before or after offering commencement, NOT the processing date. Keep effective times, evidence precision, record/discovery time, and actual reviewer/commit time separate.
- Q43: official permanent separation before BOTH external enrollment and course commencement → eligible active application auto-closes and atomically RELEASES current counted seat.
- Q44: external verified enrollment AFTER valid AKUS submission, then permanent separation BEFORE commencement → ordinary approval stops, current allocation remains counted until CURRENT authorized HoD/acting HoD verifies enrollment/separation/start evidence and formally closes/releases. Review may finish AFTER commencement per Q46; no backdating.
- Q45: permanent separation AFTER commencement → auto-close eligible active application and atomically RELEASE current seat, as narrow permanent-separation exception to Q05 voluntary withdrawal retention.
- Q47: same-date-only separation and commencement with indeterminate ordering → HOLD counted capacity for authorized HoD chronology review. If unresolved, documented HoD-authorized separation closure/release; never invent timestamp/order.
- Q41: permanently separated person no longer receives new active Silver overdue marks; preserve as-of-separation historical status.
- Q42: rehire begins a new employment episode; new subject obligations are scoped to new episode. Preserve closed old obligations and lifetime canonical course certificate/no-repeat history.
- Q48/Q49: eligible verified certificate after separation may retrospectively satisfy historical annual or subject Silver obligation ONLY if examination before separation and other conditions met, preserving earlier as-of snapshots and never reopening job, app or allocation.
- Q50: subject-wise Silver timeliness uses ACTUAL verified qualifying exam date, not certificate issuance or verification. Do not award credit before valid relevant Silver certificate verified.
- Distinguish terminal reasons: voluntary withdrawal (Q05 retention), formal academic rejection (Q06 release), integrity invalidation (Q23 release), and each separation closure path. No uncontrolled policy crossover.

### C. Integrity and late provider corrections (Q19–Q23, Q33–Q34)
- Submission MUST precede external NPTEL enrollment (Q21); legitimate later enrollment before institutional approval may be approved normally once verified (Q20).
- Missed external enrollment deadlines require legitimate extension/verified enrollment evidence, not automatic expiry (Q19).
- Later-discovered invalid enrollment chronology triggers formal integrity review: suspend institutional compliance recognition, keep existing allocation counted until authorized final resolution; if formally invalidated, atomically release even after course commencement; preserve the chronology, evidence, original approval and audit (Q22–Q23).
- Later correction from prior no-certificate to valid certificate for same canonical course triggers repeat-integrity review of newer approval, suspends its recognition while unresolved, retains quota while review pending, and follows authorized upholding/invalidation; valid upheld later application may receive appropriate credit without duplicate fulfillment (Q33–Q34).
- Avoid inventing who has academic authority to make particular evidence-review determinations when unratified. Existing HoD authority for prior unsuccessful outcomes is confirmed; general enrollment evidence verification authority is NOT globally settled. Implement safe pending/policy-gated states for unresolved cases while continuing confirmed work.

### D. Correct authority boundaries and UI flows
- Faculty and DRC Head are NPTEL applicants; Faculty → DRC Head → HoD, DRC's OWN application → HoD directly; HoD and Principal NPTEL-exempt; DRC Head and HoD appointments must never overlap for one person; Principal institution-wide oversight does not imply blanket write access; Admin has staff/master-data authority not automatic academic final approval.
- Add dedicated list/detail/reconciliation/review and evidence timeline pages appropriate to the existing approved route inventory, not generic dashboard shortcuts. Every button must invoke real guarded backend behavior, with loading/error/denial/empty/complete states, breadcrumbs and filter persistence.
- Historical reports, evidence provenance, effective-dated reviewer authority and immutable audit must remain reproducible.

## 3. Implementation practices
- Preserve FastAPI, React/TypeScript/Vite, PostgreSQL and CURRENT Docker Compose architecture, SQLAlchemy/Alembic and transactional work ledger. No new microservices or replacement stack.
- Authorize EVERY state-changing endpoint on server at commit time; apply DB constraints/locks for quota accounting and idempotency for retries, not frontend-only checks.
- Do not fabricate NPTEL external verification or live Google sign-in. If external APIs/credentials unavailable, use clearly labeled and isolated test fixtures only for automation; distinguish external acceptance from local proof.
- Unresolved policy choices (e.g., HoD topic-mapping revisions for already occupied pools, cross-year blocked-transfer final disposition, one Silver certificate across multiple subjects, IO-02 teaching import acceptance, and general enrollment-evidence verification authority) must remain POLICY_PENDING unless a subsequently ratified repository document explicitly settles them. Never invent a rule just to pass tests.

## 4. Verify actual correctness, not simply test counts
- For each vertical slice, implement migrations, service/domain logic, API, UI, audit, tests and documentation; then run targeted tests and fix failures.
- Add PostgreSQL race tests for rescheduling-vs-withdrawal/separation/rejection, concurrent transfer attempts, quota decrease, stale source metadata, source/destination occupancy, idempotent retries, blocked transfers and repeated worker delivery.
- Add branch/effective-date tests for Q43–Q47 and late evidence Q48–Q50, with historical as-of reporting.
- Run complete backend suite, frontend unit tests, mypy, Ruff/formatting, TypeScript/ESLint, production build, Playwright (including permission, responsive/accessibility checks), migration upgrade and schema-drift validation, Docker Compose health, and live quota reconciliation.
- Do not disable/skip tests or weaken assertions to conceal failures. Report executed commands and exact real results.

## 5. Durable handoff at session limits
- Update BUILD_PROGRESS.md, TEST_RESULTS.md, docs/codex/PHASE5_CHECKLIST.md (create if absent), and requirements/route/policy traceability at the end of each meaningful milestone and before prolonged test/build runs.
- Clearly list: implemented-and-verified, partial, blocked-by-external-config, POLICY_PENDING, and next exact action. Preserve code and uncommitted changes across interruptions.
- LIVE Google sign-in remains Phase 2 external acceptance work: do not claim completion without actual authorized sign-in of approved institutional accounts. Continue independent Phase 5 work.
- Do not declare global production readiness; only claim Phase 5 passed if its real acceptance checklist and tests are satisfied.

EXECUTION ORDER: Inspect existing state → verify Phase 4 gate → implement the next unfinished Phase 5 vertical slice → test/fix → update handoff → continue through remaining Phase 5 scope. Do not stop at analysis. START NOW.
