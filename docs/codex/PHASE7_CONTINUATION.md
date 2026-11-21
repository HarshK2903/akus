# AKUS — PHASE 7 IMPLEMENTATION CONTINUATION

## Purpose and execution directive
Act as Principal Software Engineer, Security Architect, Database Transaction Engineer, and Senior Full-Stack Engineer. Continue the **EXISTING** AKUS implementation in this repository. This is a **Phase 7 handoff**, not permission to recreate the application, repeat earlier phases, or declare it production ready.

**Execute approved Phase 7 work end to end** (database + backend + frontend + browser journeys + verification + documentation) using the actual repository build plan. Do not stop at drafting a plan. If a feature depends on an unratified institution policy or external authorization, implement safe pending/blocked states and continue the independent work; never fabricate an institutional decision or a live Google sign-in.

## Reported Phase 6 acceptance checkpoint (verify against the repository)
The prior Codex report states that AKUS Phase 6 met **local** acceptance criteria:
- 266 PostgreSQL backend tests passed with 4 dependency deprecation warnings.
- 2 frontend tests passed; ESLint, TypeScript, Prettier, and production build passed with a Vite bundle-size advisory.
- The interrupted Playwright full run completed with 40 passes; the affected Phase 6 tests and four additional isolated journeys passed in follow-up runs.
- Ruff, formatting, mypy, migration checks, Docker and PostgreSQL readiness checks passed.
- The final combined check exited 0. An earlier exit 1 was attributed to Prettier formatting in `e2e/phase6.spec.ts`, subsequently fixed.
- Migration head was `0018_exam_evidence`, original PostgreSQL volume preserved, with no reported schema drift.
- All 13 quota/compliance discrepancy counters were zero on the operational database and three test databases.
- Local application available on `http://127.0.0.1:8080` (actual current state must be checked).
- Real institutional Google OIDC acceptance, live certificate-provider verification and malware scanning are **NOT** independently verified. Unratified policy decisions remain open.

These are **previously reported results**. Do not assume they remain true without checking evidence and the actual working tree.

## 1. Recover safely and establish the exact Phase 7 scope
1. Work in the existing AKUS repository; locate its true root, do not assume home-relative paths.
2. Read `AGENTS.md`, `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/BUILD_PHASES.md`, latest confirmed AKUS master spec and amendments, policy register, relevant Phase 6 checklist (`docs/codex/PHASE6_CHECKLIST.md` if present), and route/requirements traceability. Inspect an existing Phase 7 checklist before creating another.
3. **Derive the authoritative Phase 7 scope from the actual repository's approved plan**, not from this prompt's examples. If Phase 7 is scoped differently from the themes below, follow the approved plan and explain the difference. Do not redo features already complete in Phases 5 and 6.
4. Inspect `git status`, staged/unstaged diffs, untracked files, migration history, Docker Compose services and volumes (read-only inspection first), app health, and final Phase 6 QA logs. Preserve all work, audit data, identity records, database schema and volumes.
5. Compare the actual implementation with Phase 7 acceptance criteria. Mark each item as verified, implemented-unverified, partial, not-started, blocked-policy, or blocked-external.
6. Record an implementation checkpoint in `BUILD_PROGRESS.md` and/or the phase checklist. Then **start implementing** the next approved vertical slice without waiting for a new instruction.
7. Never invoke `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, database drop/reset, blind seed, force migration revision, `git reset --hard`, or destructive cleanup without explicit operator approval.

## 2. Primary Phase 7 goals — only where supported by the approved build plan
Previous project phase planning has associated Phase 7 with **employment separation, rehire, historical compliance reconciliation, detailed audit and institutional reporting**. However, several elements already appeared in Phases 5–6. First inspect the actual checklist; strengthen/complete missing functionality rather than creating competing implementations.

Where Phase 7 includes these areas, implement their outstanding acceptance criteria:
- Historical staff and employment-episode transitions: joining, officially effective permanent separation, authorized corrections, later rehire, effective-dated access and appointment history.
- Consistent lifecycle handling across applications, quota allocations, pending approvals, enrollment/exam evidence, annual compliance and subject-wise Silver obligations, including races with HR updates.
- Historical compliance *as known then* versus *latest subsequently verified* reporting, preserving evidence chronology, source versions, authority and policy version. Historical corrections must append assessments; never overwrite the original as-of snapshot.
- Auditable closure/release and idempotent reprocessing with exact current quota pool accounting, including cross-year transfers and change of employment state.
- Principal institution-wide read-only oversight, HoD scoped views, DRC/Faculty personal views and Admin authority over institutional staff data (not automatic academic approval authority).
- Real multi-page UI/UX flows for the applicable cases, with accessible, functional forms, filters, paginated records, permission-safe deep links, meaningful empty/error/loading states, and no fake buttons or real-looking fabricated results.

If these are already satisfied by prior phases, mark them as **reused and regression verified**; spend effort on the genuinely remaining Phase 7 scope from the repository.

## 3. Governing institutional policies and non-negotiable boundaries
Treat later confirmed amendments as overriding contradictory historical Q-rules:
- HoD and Principal are NPTEL-exempt and do not submit personal NPTEL applications. Principal has institution-wide oversight, not unlimited mutation privileges.
- DRC Head is also Faculty and must meet NPTEL obligations. Ordinary Faculty application goes Faculty → DRC Head → HoD; DRC Head's own application goes directly to HoD; no self-approval.
- A person must **never** concurrently serve as DRC Head and HoD, including acting office appointments. Enforce over effective-dated intervals and at the database/service/authorization boundaries.
- Admin controls officially authorized staff onboarding and teaching-allocation imports via CSV/XLSX preview, validation and audited commit. A `@cmrit.ac.in` email or Google login never independently creates a role, approved appointment, teaching assignment or access.
- Shared annual quota key: department + HoD-approved primary canonical NPTEL topic + July–June academic year. An eligible submission reserves exactly one seat atomically using the approved primary topic and **published scheduled examination academic year**.
- Verified examination reschedules crossing academic years require atomic capacity-checked quota transfer. When target pool missing/full, retain source occupancy and flag case; do not overbook. Actual verified examination date separately determines annual compliance under Q35.
- Preserve Q02/Q05/Q06/Q23/Q43–Q47 quota and separation exception distinctions. Ordinary withdrawal, academic rejection, formal invalidation and institutional permanent separation have different governed effects. Exact chronology, evidence precision and approvals matter.
- Q39/Q40: subject-wise Silver obligation starts at the first official teaching assignment for a canonical subject and retains its original two-calendar-year deadline while employed despite reassignment.
- Q41/Q42: officially effective permanent separation ends active subject-wise monitoring but preserves historical status; a genuine later rehire creates a new employment episode. Reassigning the subject in that new episode creates an independently tracked obligation.
- Q48/Q49/Q50: authentic qualifying exam BEFORE separation may acquire historical annual or subject-wise Silver recognition from certificates verified AFTER separation, using actual exam dates for academic-year attribution and Silver timeliness, without reopening employment, archived apps, quotas or monitoring. Preserve immutable as-of-separation and historical reports; do not backdate review decisions.
- Enforce evidence integrity, reviewer conflict checks, effective-dated authority at decision time, idempotent transitions and append-only audit trails.
- Do not grant academic credit while corresponding integrity-review suspensions remain active or formally invalidated.

**DO NOT arbitrarily settle unresolved decisions.** At minimum check the current policy register for: IO-02 (teaching import HoD confirmation), whether a later primary-topic mapping change affects existing reservations, how a permanently blocked year-transfer case gets finally disposed, Q51 reuse of one Silver certificate for multiple subject obligations, exact authority for general certificate/enrollment evidence verification, and any calendar-edge rules or external verification policy. Implement defensible pending states, permission-safe UI and clear requirements coverage rather than silently choosing.

## 4. Backend/database engineering and failure-mode requirements
For every approved Phase 7 transition:
1. Identify the authoritative source, effective date precision, observed/recorded timestamp, immutable source snapshot, policy version and the responsible actor/office appointment.
2. Use database transactions and consistent row lock order for conflicting employment, approval, quota and evidence operations; never assume frontend pre-checks are sufficient.
3. Implement exactly-once/idempotent mutation semantics, stable operation identities, constraints/uniqueness and transactional audit + work-ledger enqueue.
4. Keep domain state machines distinct: employment; applicant eligibility; application; quota allocation; provider exam/enrollment; certificate evidence; annual compliance; Silver monitoring; and case review.
5. For historical corrections, append a superseding evidence/assessment/reconciliation result with provenance. Do not delete former decisions, recreate closed applications, convert stale events into current facts, or rerun bootstrap seeds against real data.
6. Never introduce an external HTTP call inside an open PostgreSQL transaction. Real external source verification should have failure-safe pending states, bounded retries, and clear source reliability.
7. Build safe Alembic migrations compatible with the current persistent database and a clean test database. Validate downlevel/upgrade history without dropping real data.
8. Cover concurrency: HR separation racing with approval; certificate review racing with integrity hold; competing quota release/transfer operations; same-day uncertain event order; revised teaching assignments; rehires; repeated worker delivery; stale authority revocation; historical report queries before/during/after corrections.
9. Implement authorization in FastAPI at the action/resource/department/office level; UI concealment alone is insufficient.

## 5. Required user-facing experiences where in scope
Follow the route inventory in the repository rather than inventing arbitrary URL structures. Implement and validate all phase-approved pages and meaningful user journeys:
- Faculty/DRC personal status, prior episodes and certificates, closure and historical assessments, case histories and evidence links.
- HoD task reviews for institutionally authorized cases, current department staff, exception and reconciliation queues.
- Admin staff and official history management, effective-dated corrections, separation/reappointment workflows, import evidence and audit trail.
- Principal cross-department reports, historical as-of versus latest-verified views, exceptions and compliance overview with read-only authorization unless an explicitly confirmed exception grants more.
- Evidence display must accurately distinguish actual vs scheduled exam, external enrollment vs institution approval, date-only vs exact timestamp, verification vs claimed evidence, original vs corrected decisions.
- Every displayed metric must be backed by actual database queries (or be explicitly labeled fixture/demo), not hardcoded institutional numbers.

## 6. Existing Docker and operational constraints
- Continue using the existing Docker/Compose app; don't introduce a native-Linux duplicate or select the final production hosting method.
- Preserve original PostgreSQL volumes and production-like local data; never run destructive environment cleanup without approval.
- Inspect current Compose service names and health before rebuild/restart; run only necessary safe operations.
- Keep OAuth secrets in protected env/config, never output them in logs, patches, test snapshots or commits.
- Real Google OIDC sign-in for five authorized institutional test people remains **EXTERNAL UNVERIFIED** until approved OAuth credentials, official appointments and voluntary account-holder login are available. This does not automatically block independent Phase 7 development.
- Live NPTEL provider certificate authenticity verification and malware scanning remain unverified until demonstrated; do not call simulated flows 'live verified'.

## 7. Acceptance tests and quality bars
1. Implement actual tests for Phase 7 behavior, including positive paths, policy-blocked paths, unauthorized actions, import/correction history, idempotency, race conditions and historical snapshots.
2. Run backend PostgreSQL tests; frontend unit tests; Playwright browser flows including accessibility and responsive views; Ruff/mypy; ESLint/TypeScript/Prettier; production builds; safe Alembic migrations; Docker health checks; source/audit/quota/compliance reconciliation.
3. Fix failing tests and actual defects; **do not delete, skip, weaken or relabel tests to obtain a green result**.
4. Distinguish real tested provider/OIDC integration from controlled fixtures and mocks.
5. Verify any earlier warnings: distinguish benign dependency deprecations, performance/bundle-size advisories and actionable regressions. Do not misreport warnings as test failures or silently hide them.
6. Keep live read/write acceptance confined to authorized test data and users. Don't impersonate actual Google account holders.
7. Inspect exact test logs and exit codes, not merely an intermediate 'All checks passed' line.
8. Before claiming Phase 7 complete, publish a row-by-row traceability and acceptance summary with evidence/test commands and real pass counts. State clearly what depends on unratified policy or external authorization.

## 8. Progress persistence and recovery
At the start and **after EACH meaningful passing vertical slice**, update `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, actual Phase 7 checklist (under `docs/codex/`), and route/policy traceability as appropriate. Include actual migration head and test commands/results. Preserve task status in the repo because Codex sessions can be interrupted by usage limits.

If running low on model budget, prioritize (1) saving a durable accurate progress checkpoint, (2) completing the current small vertical slice, (3) tests and a precise next action. Don't launch a long test command when unable to capture or inspect its outcome. Do not claim a background command will complete after this session without monitoring.

## 9. Final report format and execution instruction
Report:
- Actual recovered checkpoint and existing work preserved.
- Phase 7 approved requirements and coverage status (including what was already implemented in earlier phases).
- New migrations/models/APIs/UI/tests delivered.
- Test counts, command exit statuses, Docker/service/migration/data checks and logs.
- Exact external/institutional policy blockers (Google live login, provider authenticity, unresolved policies, etc.).
- What remains for the next phase and whether Phase 7 **local** acceptance genuinely passed.

**START NOW: inspect repository state and Phase 7 plan; implement every achievable approved Phase 7 requirement in verified vertical slices; do not stop at planning.**
