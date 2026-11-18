# AKUS — Recover Current Checkpoint, Finish Achievable Phase 2 Work, and Implement Phase 3

You are a principal software engineer, software architect, security engineer and senior full-stack implementation agent working INSIDE MY EXISTING AKUS REPOSITORY. This is continuation of a real project, NOT a new application, migration to a new stack, or rewrite. Implement code and test it; do not stop after a plan.

## 1. Recover the exact current project state

Before editing anything, read and reconcile all available files, including:

- `AGENTS.md`
- `BUILD_PROGRESS.md`
- `TEST_RESULTS.md`
- `docs/codex/PHASE2_COMPLETION.md`
- `docs/codex/PHASE2_CHECKLIST.md` (if present)
- `docs/codex/BUILD_PHASES.md` (if present)
- The latest AKUS master specification and comprehensive UI/UX blueprint under `docs/spec/`, or their actual locations in this repository
- `docs/GOOGLE_OIDC_SETUP.md` (if present)
- Relevant architecture, policy decisions, and existing route inventory

Inspect actual current branch and `git status`, existing changes and untracked files, migrations, Docker Compose config, services and logs. Do not assume files are committed. Preserve code, database records, backups, working Docker volumes and existing OAuth configuration. Do not run `git reset --hard`, `git clean -fd`, `docker compose down -v`, `docker volume prune`, database resets, or similarly destructive commands. Do not choose production deployment now.

The previous Codex session reported checkpoint `034f71a`, application `http://127.0.0.1:8080`, 109 backend tests, 2 frontend tests and 28 Playwright tests passed; formatting, lint, type checks and production builds passed; four Docker images built; API/DB healthy; existing and fresh databases migrated to `0006_identity_history` with no schema drift. This is a PREVIOUS REPORT, not current verification. Recheck the actual repository and repeat relevant checks. Preserve all completed Phase 2 features.

## 2. Finish or correctly isolate Phase 2 acceptance blockers

The main incomplete acceptance gate is live institutional Google OIDC verification with real account-holder participation. The intended authorized real-person UAT roster is:

| Role | Intended Google account |
|---|---|
| Faculty | `faculty-harsh1.cse24@cmrit.ac.in` |
| HoD | `hod-ankit.cse24@cmrit.ac.in` |
| DRC Head | `DRC-awanish.cse24@cmrit.ac.in` |
| Admin | `admin-harsh.cse24@cmrit.ac.in` |
| Principal | `principle-nikshay.cse24@cmrit.ac.in` |

Verify approved roster/appointments before provisioning privileges. A matching email or `@cmrit.ac.in` domain does not grant roles. Real Google login requires authorized OAuth client configuration and voluntary account-holder participation; never ask for passwords, impersonate account holders, bypass authentication, or fabricate a successful live login. Use immutable Google `sub` for durable identity links; enforce issuer, audience, signature, expiration, state, nonce, PKCE as appropriate, hosted-domain claims, server sessions and CSRF protections. Follow `docs/GOOGLE_OIDC_SETUP.md` for actual project callback and Docker host/port. Keep credentials in private environment, not Git, prompts or logs.

If live Google credentials, institutional approval, or an account holder is unavailable, document the precise external blocker; keep live UAT UNVERIFIED and continue independent development. Confirm whether any locally achievable Phase 2 work actually remains incomplete; implement and test it. Don't claim Phase 2 entirely complete while mandatory external acceptance remains unverified.

## 3. Start Phase 3 — implement NPTEL courses, topics, mappings, annual quotas

Read the repository's actual phase plan, route inventory and latest institutional amendments before choosing endpoints or paths. Build each vertical slice end-to-end: PostgreSQL migration and invariants, FastAPI domain implementation, authorized API, real React page, full empty/loading/error states, integration tests, browser tests and documentation.

### NPTEL canonical course and offering registry

Implement correct separation of canonical course identity and specific NPTEL offering/run. Store course identity, title, description, duration, listed provider categories (possibly several), exact offering IDs, start/end dates, enrollment deadline, exam-registration deadline, published/scheduled examination date, and authoritative metadata provenance, version and time last checked. Provider integration may be fallible: handle unavailability, bad response/schema changes, and source conflicts honestly; never assume a published scheduled examination proves actual exam participation or certificate attainment. Preserve history and original submission snapshots.

### Topic registry and approved primary charging topic

Maintain canonical institutional topics and normalized provider category aliases. A course may list several NPTEL categories. For each (department, canonical NPTEL course), the CURRENT authorized HoD or acting HoD approves EXACTLY ONE primary charging topic on academic grounds; preserve evidence, authority snapshot, effective-dated revisions and append-only audit. Apply it consistently to offerings while effective. Different departments may adopt different justified mappings. Faculty and DRC Head cannot switch categories to evade full quotas. When mapping is missing, permit draft and deduplicated HoD mapping request, but do not claim successful submission or reserve a seat. Concurrency-safe mapping revision and application submission must revalidate effective revisions. Do not invent retroactive movement of existing seats when the mapping changes: this institutional policy remains unresolved.

### Annual shared departmental topic quotas

The authoritative quota key is (department, approved canonical NPTEL topic, institutional academic year July 1 through June 30). HoD configures, publishes and audits quota maximums and revisions for each key. Different courses mapped to the same pool share its capacity. HoD may increase; decreases cannot go below counted HELD/CONFIRMED/retained seats. No publication means no successful submission. Do not resurrect superseded per-offering quota rules. Implement authorized list/detail/edit/publish, occupancy, allocation history and reconciliation screens.

### Submission-time eligibility and reservation boundary

Use the officially published SCHEDULED EXAM DATE current at valid submission to determine intended annual quota pool. Apply all existing eligibility and due-date rules, correct departmental mapping and published pool, then atomically reserve one seat on successful valid application submission. Store immutable source date, metadata snapshot, mapping version, quota pool and policy context. No double reservations across retries, concurrent submissions or first/last seat races. Actual verified exam date later determines final annual NPTEL compliance year under confirmed Q-35, and is not interchangeable with scheduled exam date.

### Official cross-year exam rescheduling

If NPTEL verifiably reschedules the published exam across July–June year boundary, attempt a capacity-checked atomic transfer of each affected counted reservation from source department-topic-year pool to destination published pool for the newly scheduled year. Lock both pools deterministically, transfer exactly once, update current allocation pointer and append movement/audit/outbox evidence in one PostgreSQL transaction. If target missing, unpublished or full: keep original reservation counted, create auditable reconciliation case, notify correct institutional authority; never partially transfer, overbook, silently release or invalidate application. Repeated/out-of-order reschedule events must be idempotently reconciled. Current actual verified exam date remains source for final compliance even if transfer blocked.

## 4. Preserve role hierarchy and policy precedence

Newer governing policies override contradictory historical master policy rows:

- Ordinary Faculty must do NPTEL; normal approvals Faculty -> DRC Head -> HoD.
- DRC Head is Faculty and must do NPTEL; own applications go directly to HoD, never self-review.
- HoD is exempt from personal NPTEL applications and is the departmental final approver, quota owner and topic mapping authority.
- Principal is exempt, has institution-wide read oversight/reporting, without implied unconstrained academic write authority.
- DRC Head and HoD must NEVER be the same person, including effective-dated and acting appointments; enforce in DB, API and UI.
- Admin controls verified institutional roster, official CSV/XLSX teaching data import, corrections and authority records, but has no academic approval rights merely through Admin role.
- Do not decide unresolved IO-02 teaching-import signoff, retroactive topic-mapping migration, or reuse of one Silver certificate for multiple subject obligations. Use explicit pending/configuration-gated behavior when needed.

Do not break immutable audit, effective-dated organizational history, certificate verification, annual/Silver compliance, quota state machine, separation/rehire exceptions or previously implemented Phase 2 identity/provisioning features.

## 5. Implement complete professional pages and workflows

Use the specified restrained light-theme multi-page UI/UX system; follow the actual route inventory. Deliver functional course discovery, course detail, provider categories, canonical topic list/detail/proposals, departmental course-to-topic mappings and HoD review, annual quota listings, detail/editor/publication and occupancy/audit, cross-year transfer/reconciliation views, plus related navigations and permission-driven actions. Real backend data only; no fake green statuses, dead buttons, invented success, decorative dashboards, or hidden permission bypass. Handle accessible keyboard focus, responsive tables/forms and truthful loading/empty/error states.

## 6. Maintain existing Docker deployment for development

Keep the actual Docker-based development project. Inspect service names, networks, Compose config, files and volumes before commands. Preserve existing Postgres persistent data. Do not force native-Linux setup, create a competing project, delete volumes or choose final production hosting. Run incremental safe migrations. Maintain usable Google callback redirects through the browser-facing host (not internal container names).

## 7. Test each implementation slice; preserve resumability

For each working slice, run applicable backend unit/integration/concurrency tests, frontend tests, Playwright E2E tests, lint, Ruff formatting, TypeScript checks, production build, migration checks and Docker service health checks. Fix failing tests rather than reporting them as passed. Test last-seat race, mapping revision race, quota decrease, invalid provider categories, absent quota, rescheduling target full/unpublished, retry/idempotency, concurrent closure and correct permissions. Never manufacture test results.

Update `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, current Phase 3 coverage checklist, policy/route traceability, and integration guides after progress so a new Codex session can pick up from files. State separately: implemented/verified, implemented/unverified, pending institutional policy, blocked external Google client/account holder, not implemented. Do not claim full AKUS production readiness or Phase 2 live UAT complete without evidence.

## 8. Execute now

Start by inspecting repository state and latest documents. Verify previous checkpoint, finish any achievable residual Phase 2 tasks, then BEGIN implementing Phase 3 immediately; do not stop after an outline. Work through the remaining achievable Phase 3 requirements as far as runtime context and permissions allow. If external Google configuration is unavailable, record that blocker and continue. Preserve existing files and data, run tests and repair failures, and leave an accurate progress checkpoint when done.
