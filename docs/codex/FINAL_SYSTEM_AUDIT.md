# AKUS — FINAL FULL-SYSTEM ACCEPTANCE AUDIT AND IMPLEMENTATION HARDENING

## Role and nonnegotiable objective

Act as a Principal Software Engineer, Senior Application Security Engineer, Staff Database Engineer, Test Architect, and UI/UX Quality Lead **inside my existing AKUS Git repository**. This is a continuation of the existing implementation, **not** a greenfield project or a request for a theoretical design report.

**Goal:** Independently audit the complete AKUS application against its current confirmed institutional policies, build plan and UI/UX specification; reproduce actual checks; repair proven defects and omissions safely; document evidence, external blockers and production-readiness gaps. **Do not declare full institutional or production readiness until every required real-world gate has been met.** Implement all independently achievable fixes, not just findings.

## Last reported checkpoint — verify from repository and logs before relying upon it

The previous Codex session reported **Phase 8 local acceptance passed**:

- 316 PostgreSQL backend tests passed, with 2 dependency deprecation warnings.
- 3 frontend tests passed; Ruff, mypy, ESLint, TypeScript, Prettier and production build passed.
- 52 standard Playwright journeys and 4 isolated journeys passed, including the 320px evidence-page accessibility case.
- All 80 specification paths resolved; browser sweeps opened all 51 protected paths; anonymous-access tests covered 114 protected API operations.
- Docker images built; startup and migrations succeeded; API healthy; current worker heartbeat; original PostgreSQL volume preserved at Alembic head `0021_application_files`.
- All 22 quota, compliance, employment and audit discrepancy counters were zero across eight databases. Two synthetic restore checks reproduced application and certificate-evidence manifests.
- A duplicate vacant-HoD alert from repeated scans was fixed. Evidence PDF private upload/replacement/draft removal, evidence revision references, owner authorization, quarantine and private cache headers were implemented.

**These are reported results, not proof you have personally rerun them.** Inspect and revalidate them. If reality differs, report the discrepancy instead of restating the checkpoint as fact.

## 1. Recover the exact live repository state safely

1. Read `AGENTS.md`, `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/BUILD_PHASES.md`, the actual Phase 8 checklist, requirement traceability, the latest AKUS master specification, the UI/UX blueprint, security docs, Docker/Compose configuration, and current operating runbook. Discover actual filenames where they differ; never assume nonexistent paths exist.
2. Inspect `git status --short --branch`, recent commits, uncommitted diffs, untracked files and the precise running images, services, migrations, ports and database connections. Preserve unfinished user work.
3. Take non-destructive snapshots/backups where supported, verify backup metadata and permissions, and inspect existing rollback procedures **before any migration or potentially state-changing command**. Avoid copying real secrets/PII into reports.
4. Never run `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, database wipe, destructive migrations, or `git reset --hard`. Do not rotate/replace credentials or change production hosting without my explicit authorization.
5. If the reported Phase 8 task is incomplete, finish and verify it first; do not invent a later phase. Consult the actual build plan before calling anything Phase 9.

## 2. Establish one authoritative requirements and policy baseline

Reconcile older policy rows with later confirmed amendments. Do **not** turn previously proposed options into binding policy. Maintain a versioned precedence register: confirmed current policies, superseded policies, pending institutional decisions and externally unverifiable assertions. Cite exact repository source locations in your coverage report.

Current overriding institutional constraints include:

- Faculty and DRC Head (who remains a faculty member) require applicable NPTEL participation/compliance. HoD and Principal are NPTEL-exempt and have no personal applicant workflow.
- Faculty application routing: Faculty -> DRC Head -> HoD. DRC Head's own application -> HoD directly; no self-review. DRC Head and HoD must always be different persons including acting appointments. Principal has institution-wide oversight without unrestricted academic write permissions. Admin manages authoritative data but does not inherit academic approval.
- Approved staff identities, effective-dated offices and teaching assignments, secure controlled Google subject linking, CSV/XLSX staff/assignment import and auditable corrections. Email-domain membership alone is not authorization.
- Shared published quota pool key: department + HoD-approved canonical primary topic + July–June academic year; approved primary topic mapping per department and canonical course; valid submission atomically reserves one seat; the scheduled exam date at submission identifies the initial quota year.
- Verified exam rescheduling across academic years: capacity-checked atomic transfer; on missing or full target pool, retain original occupancy and flag reconciliation. Actual verified examination date governs final annual compliance credit.
- Q-02 through Q-50 remain valid only where compatible with later amendments; use current registry to adjudicate actual scope. Certificate and Silver obligations require genuine evidence, strict deadline and subject relevance checks, as-of reporting and effective-dated employment handling.

**Explicitly pending, unless the repository documents later ratification:** IO-02 teaching-assignment activation authority; Q-51 multiple-subject Silver certificate reuse; retrospective HoD topic-mapping migration; final disposition of indefinitely blocked quota transfers; general enrollment/certificate evidence-verification authority beyond separately confirmed powers. No policy guessing. Keep affected decisions safely pending but complete independent work.

## 3. End-to-end functional verification — actual data, routes and server authorization

Build a **requirement -> database model/migration -> backend service/API -> permission -> UI route/action -> test -> observed result** traceability matrix. Verify more than route existence: genuinely execute workflows, reload and check persisted state, use realistic authorized test fixtures, navigate error/retry/empty/loading states, and inspect audit/ledger entries.

Cover at minimum:

A. Identity, onboarding and staff lifecycle: first-Admin bootstrap, approved roster import, row-level validation, duplicates, staged preview and explicit commit, audited corrections, effective-dated teaching, current appointments, DRC/HoD mutual exclusion, employment episode separation/rehire, disabled user access and first Google subject linking.

B. Five role journeys and negative permissions: Faculty, DRC Head, HoD, Admin, Principal. Verify navigation, list/detail pages, action links, deep-link 403/404 behavior and backend denial despite manipulated frontend. Validate Principal global read visibility without unapproved write privileges, HoD/Principal applicant exemption, DRC direct-HoD self-application and ordinary Faculty DRC -> HoD routing.

C. Course and quota: canonical courses vs offerings, provider category aliases, one approved department primary charging topic, topic intake, published annual pool, quota changes, last-seat concurrent submissions, idempotency, source snapshot changes, scheduled/actual exam dates, deadline eligibility, blocked cross-year transfers, eventual quota availability, source-versus-target pool consistency, simultaneous transfer/withdrawal/separation.

D. Application lifecycle: draft/submission, approval/rejection, unverified prior results, canonical no-repeat after certificate, external enrollment chronology, late deadline evidence, voluntary withdrawal before and after commencement, permanent separation scenarios Q-43–Q-47, chronology ambiguity, split authority and HoD turnover/vacancy, later integrity review/invalidation and quota release. Verify exactly-once reservations, no stale HoD approval, immutable evidence and audit.

E. Evidence, compliance and historical reporting: private PDF upload/replace/remove, safe MIME/content limits and quarantine, subject-specific certificate evidence, annual >=8-week OR two valid 4-week offerings in same examination year, 75% Silver subject criteria, Q-39/Q-50 two-calendar-year exams, separation/rehire and retrospective Q-48/Q-49 recognition, certificate corrections/revocations, no duplicate fulfillment and as-of report reconstruction.

F. Complete UI/UX inventory: compare actual 80 paths and repository page specs, responsive navigation and content density, tables/filters/sorting/search state preservation, form validation, clear authorization and status explanations, empty/error states, keyboard focus, mobile widths and accessibility semantics. Do not count a page as complete merely because it renders a generic layout.

G. Notifications, work ledger and background jobs: retries, deduplication, exactly-once domain transitions, appointment/vacancy notifications, processing latency, retry safety and app recovery after worker/process restarts.

## 4. Security and privacy validation

- Review authentication state/nonce/PKCE/code callback logic, JWT/ID-token validation against issuer/audience/expiry/email_verified/hosted domain and Google immutable `sub` linkage; session, CSRF, Origin, cookie Secure/SameSite/HttpOnly, logout, timeout and revocation. Inspect test doubles distinctly from live OIDC.
- Test IDOR, RBAC/ABAC permission escalation, cross-department access, staff deactivation, reviewer self-approval, stale role appointments, route-level exposure and write/read authority separation.
- Audit source-provided NPTEL metadata and uploaded documents as untrusted inputs: injection, path traversal, PDF payload, content spoofing, malware handling, private downloads, content caching, access logs and excessive debug output.
- Ensure no actual staff credentials, OAuth secrets, PII exports, tokens or cookies appear in Git history, logs or downloadable evidence. Use an appropriate reputable secrets-scanning tool if available, and accurately characterize any scan's limitations.
- Validate database transactions, SQL concurrency, migration safety, outbox idempotency, effective-dated invariants, immutable history and recovery/restore. Check dependency advisories and configuration hardening; record remaining gaps by severity and exploitability.
- No production OAuth bypass or hardcoded role mappings. Never impersonate real staff.

## 5. External verification gates — track separately and never fabricate

**Real Google OAuth / five real people:** verify client and browser-facing callback against actual reverse proxy/origin; produce a secure admin-controlled authorization and staff-provisioning checklist for these intended test accounts: `faculty-harsh1.cse24@cmrit.ac.in` (Faculty), `hod-ankit.cse24@cmrit.ac.in` (HoD), `DRC-awanish.cse24@cmrit.ac.in` (DRC Head), `admin-harsh.cse24@cmrit.ac.in` (Admin), `principle-nikshay.cse24@cmrit.ac.in` (Principal). These are **real named acceptance targets**, not proof of account ownership or authority. Actual login requires approved OAuth configuration, independently confirmed institutional appointments and the voluntary participation of each account holder. Never request passwords; do not make up sign-in successes. Record which identities completed actual OIDC only after that occurred.

**Live NPTEL provider and certificates:** distinguish publicly fetched course metadata from authenticated per-person enrollment or certificate verification. Confirm real provider access only when available; do not claim certificate authenticity from PDF format alone. Treat external verification unavailable as a documented acceptance blocker.

**Evidence malware scanning:** verify the actual deployed scanning engine and quarantine-to-verification handling; local placeholder checks are not proof of deployed scanning.

**Unratified policies:** mark as pending; create a policy-decision backlog with exact blocked actions but do not allow unconfirmed authority to mutate institutional records.

**Deployment and governance:** the development runtime is the user's existing Docker environment; production hosting remains undecided. Do not confuse passing local Docker and browser checks with production readiness.

## 6. Execute real tests and fix defects

Run the repository's actual test and quality commands, choosing safe non-destructive operations. Include:

1. Backend PostgreSQL tests with transaction/concurrency assertions and existing migration checks.
2. Frontend unit tests, ESLint, TypeScript, formatting and production build.
3. All Playwright smoke, role, academic, evidence, 320px mobile, keyboard and isolated sensitive-case journeys.
4. Docker Compose build/start/health and worker heartbeat (no volume deletion), then verify API and frontend through the real browser-facing origin.
5. Database reconciliation SQL and period-specific historical as-of reporting invariants.
6. Restore/backup rehearsal on isolated synthetic/test databases, only with safe approved setup; do not overwrite operational data.
7. Performance/size review, dependency deprecation analysis, common security headers, accessibility and meaningful error reporting.

If a test command fails: capture exact command, exit status, logs, root cause, fix and rerun. Do not remove assertions, disable failing tests, or redefine coverage to declare success.

Checkpoint progress after **each completed, verified vertical slice** in `BUILD_PROGRESS.md`, `TEST_RESULTS.md` and an audit journal. Use small coherent commits only if repo convention and user approval support them; never conceal unrelated uncommitted changes.

## 7. Deliver a final evidence-backed audit package

Create/update in the repository (adapt exact paths to existing conventions):

- `docs/qa/FINAL_ACCEPTANCE_REPORT.md`: executive result, exact checked commit/worktree state, tested environment, evidence links, major defects fixed, unresolved risks and **LOCAL PASS / EXTERNAL BLOCKED / NOT READY** distinctions.
- `docs/qa/FINAL_REQUIREMENTS_MATRIX.md`: each confirmed requirement/route/policy linked to implementation and executed verification evidence; all gaps explicit.
- `docs/qa/SECURITY_REVIEW.md`: threat scenarios, findings, authorization test results, secret/config review, residual risk.
- `docs/qa/GOOGLE_REAL_USER_UAT.md`: safe steps and per-role acceptance statuses (unverified until actual sign-in).
- `docs/qa/EXTERNAL_DEPENDENCIES_AND_POLICIES.md`: Google OAuth, official roster, provider verification, scanning, unresolved decisions and production deployment decisions.
- `docs/qa/RELEASE_READINESS_GATE.md`: go/no-go checklist with specific evidence and owners; **DO NOT mark production-ready while mandatory external and policy gates remain open**.
- Keep `BUILD_PROGRESS.md`, `TEST_RESULTS.md` and requirements traceability synchronized.

In your final response, summarize real command/test counts, fixed defects, preserved data/migrations, confirmed local functionality, blocked live integrations, unresolved policies and exact remaining institutional actions. If a required item cannot be completed now, leave a precise actionable blocker and proceed with all independent work. Do not promise work later or pretend to run in the background.

**START NOW.** Inspect current repository, verify the Phase 8 checkpoint, run the full-system audit, fix actual issues, gather evidence and document a truthful release gate. Do not stop at planning, do not reset the database, and do not claim institutional/production acceptance from local-only checks.
