# AKUS Codex project instructions

## Governing specification
- `docs/spec/AKUS_MASTER_SPEC.txt` is the binding, self-contained functional + architecture + UI/UX specification. It embeds the blueprint and approved latest V2.4 amendments.
- `docs/spec/AKUS_UIUX_BLUEPRINT.md` is a readable duplicate of the UX blueprint, useful for focused design work. Never interpret duplication as a second conflicting policy source.
- The user-confirmed 2026-11-18 hall-ticket scheduled-date verification clarification is recorded in `docs/policy/HALL_TICKET_AUTHORITY_2026-11-18.md`: current department HoD may authenticate person-specific official schedule evidence; all other unresolved verification authorities remain pending.
- Newer explicitly binding institutional overrides inside the master spec take precedence over historical Q01-Q50 rules. Historical rules must be retained for traceability but disabled when superseded.
- Unresolved rules are NOT permission to invent policy. Use safe blocked `POLICY_PENDING` decisions, tests and an unresolved register.

## Required system
- Build a real working, professionally designed LIGHT-THEME, MULTI-PAGE AKUS NPTEL application: React 19/TypeScript/Vite/React Router/TanStack Query frontend, FastAPI/Python 3.13/SQLAlchemy sync/Psycopg 3 backend, PostgreSQL authoritative database, documented reproducible dev setup. Follow the master spec for precise stack choices and alternatives.
- Applicant roles: Faculty and DRC Head (who is faculty). HoD/acting HoD and Principal are NPTEL-exempt; HoD and DRC Head are never the same person. Ordinary faculty review: DRC -> HoD; DRC applicant review: HoD directly. Principal has institution-wide oversight without blanket write authority.
- Quota pools are department + approved canonical primary NPTEL topic + July-June academic year; HoD publishes the cap. Initial reservation charges scheduled-exam year. Confirmed cross-year official reschedules require atomic capacity-checked transfer, retaining old counted occupancy on failure. Distinct from actual-exam-year compliance. No successful submission without quota/topic and atomic reservation.

## Working agreement
- Inspect the repository and specifications before changes. Maintain `BUILD_PROGRESS.md`, `POLICY_GAPS.md`, `TEST_RESULTS.md`, `docs/implementation-plan.md`, and a requirements-to-code/test traceability matrix.
- Implement complete VERTICAL SLICES: schema+migrations, APIs, service logic, frontend routes, real user actions, tests and running proof before starting the next slice. Do not create 80 decorative pages with mock buttons.
- Keep modules modular and server-authoritative; role guards in UI are not security. Always enforce current effective-dated permissions and conflict-of-interest checks at API/transaction layers.
- Use PostgreSQL transactional updates, immutable event/audit history, idempotency, and concurrency tests for quotas, topic mapping revisions, approvals and cross-year migration.
- Build actual browser navigation with Playwright end-to-end and responsive screenshots. Provide demo fixtures that are conspicuously LOCAL/DEMO; never present fake Google OIDC/NPTEL certificate validation as genuine.
- Run build, lint, typecheck, migrations, backend tests, UI tests and browser smoke tests regularly; record actual commands and results, not aspirational 'passed' claims.
- Do not delete specs, secret-scan output, audit facts, or existing project functionality. No destructive operations, credential exposure, deployment or external account changes without explicit permission.
- Before the end of each slice, summarize changed files, verified tests, demo steps, blockers and next slice; continue to the next unfinished item when explicitly asked.
