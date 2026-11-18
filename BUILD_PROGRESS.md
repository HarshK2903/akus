# AKUS Phase 3 — verified local checkpoint, 2026-11-18

**Phase 3 catalog/topic/annual-quota core and the continuation's admission/transfer
slice are implemented and locally verified.** Mandatory Phase 2 real Google UAT
remains externally BLOCKED/NOT VERIFIED. Full AKUS evidence/compliance/lifecycle and
all 80 mature page contracts are not complete; this is not production readiness.

## State recovered and preserved

Recovered main/034f71a with extensive tracked/untracked work, migrations 0007–0010,
existing Compose topology and original `akus-local_akus_pg` (created
2026-11-16T00:36:02+05:30). No reset, clean, volume deletion, database reset or agent
commit. Services were stopped after the host interruption and restarted safely.
The old /tmp final-check log was absent; new evidence is durable under docs/qa.
Previous progress/results are retained below and in docs/qa/phase3-recovered-*-history.md.

## Repaired in this recovery

- Reproduced the withdrawal-first ordering deterministically: a new exam-only source
  observation marked the whole offering conflicted and incorrectly rejected lawful
  withdrawal with VERIFIED_COMMENCEMENT_REQUIRED. The original concurrent test passed
  five pre-fix repetitions; this did not disprove the race. The new ordered regression
  failed before the repair; its full traceback is retained.
- Withdrawal now uses fresh accepted commencement only if all newer observations agree
  on that start date. Actual start-date conflict/unavailable/stale evidence still blocks.
  Existing offering/application/current-pool locking, idempotency and deferred ledger
  constraints are intact. Audit records commencement snapshot/digest/date. Original
  failing test was not weakened, skipped or deleted. No double-decrement was observed;
  both transaction orderings now give lawful exactly-once current-pool release.
- Released allocations close pending schedule/transfer work with an explicit
  no-evidence-or-policy-decision reason; original claims/notices remain immutable.
- Added authorized `/quota-transfer-cases/{id}` and usable HoD/Principal case deep link,
  target quota navigation, source workspace `/admin/nptel-sync` and metadata versions
  `/admin/nptel-offerings`. Added scope/browser checks and refreshed OpenAPI/TS types.
- Fixed an ambiguous legacy Playwright employment-date selector by scoping it to the
  employment history region. Corrected academic checkbox layout, empty allocation
  state and stale planned/Phase 2 UI copy; inspected actual desktop/mobile screenshots.
- Exposed engineering provider freshness TTL through existing Compose/.env.example.
  Refreshed persistent implementation, policy/route coverage and source/setup guides.

## Working end-to-end

Catalog separates canonical courses from exact runs with real bounded public NPTEL
metadata, immutable source versions and honest stale/conflict/error states. Topics,
aliases/proposals and current HoD effective one-topic mapping are functional. HoD
publishes department/topic/July–June annual pools; courses share capacity. Missing
mapping/cap keeps drafts unsubmitted; Faculty cannot choose the charging topic.

Valid first-attempt admission atomically creates one HELD allocation and immutable
submission/source facts. Ordinary Faculty review is DRC→HoD; DRC own is directly HoD;
no self-review, HoD/Principal applicants or Admin academic power. Lawful withdrawal
and rejection release the current pool; post-start withdrawal retains count. Cross-year
provider changes transfer atomically with balanced ledger, or retain source and flag
missing/unpublished/full target. Durable worker rechecks and in-app notices are real.

The user-confirmed current HoD authority supports independent person-specific official
hall-ticket scheduled-date authentication, immutable source reference/digest/time and
exact-person movement. Faculty claims alone cannot transfer. Actual examination,
certificate attainment and annual/Silver credit are never inferred from schedule data.

## Verified gates and running application

- **177 backend PostgreSQL tests passed**, 2 dependency deprecation warnings; Ruff lint,
  66 Python files formatted, mypy 48 modules, migration/drift checks passed.
- Frontend ESLint, TypeScript, Prettier, **2 Vitest tests**, Vite production build passed.
- **33 Playwright tests passed** on compiled Docker/Caddy/API/PostgreSQL, including
  five Phase 3 journeys, original source workflows, accessibility and responsive proof.
  The final system-page copy correction also passed its **12 affected browser tests**.
- Existing api/migrate/worker/web images built; API/DB healthy, worker/web/proxy running,
  migrate exit 0. Existing and newly created isolated fresh DB reached
  **0010_personal_schedule**, no drift; fresh startup seed twice passed.
- Frontend HTTP 200 at **http://127.0.0.1:8080**; API docs `/api/docs`. Live aggregate
  quota count/ledger check: **0 inconsistent pools, 0 invalid transfer pairs**.
- Real public `noc26_cs98` fetch succeeded, OFFICIAL_HTTPS with digest and normalized
  metadata. It remains unaccepted historical source, not enrollment/certificate proof.
- Complete master/embedded blueprint inventory (2,607 lines, 80 routes, 50 historic
  policies) and original hashes unchanged; limited secret scan: 90 files, 0 matches.

Exact commands, failures, final logs and limits: [TEST_RESULTS.md](TEST_RESULTS.md).
Requirement classifications: [Phase 3 checklist](docs/codex/PHASE3_CHECKLIST.md).
Demo and real public-source steps: [NPTEL guide](docs/NPTEL_PROVIDER_SETUP.md).

## Remaining blocks and next executable slice

**External:** real Google Web client ID/secret, registered browser callback/private
session key, approved five-person roster/appointments and voluntary account-holder
sign-ins. `google_enabled:false`, 0 external identity links; all five real UATs unverified.
Use docs/GOOGLE_OIDC_SETUP.md; do not fabricate facts, log in for users or bypass auth.

**Policy:** cross-topic existing-seat revisions, permanent failed-transfer remedy/
priority, exemption transitions/emerging exceptions, IO-02/P-54/Q51 and remaining
unratified authorities stay POLICY_PENDING. HoD hall-ticket schedule authority is
confirmed only within docs/policy/HALL_TICKET_AUTHORITY_2026-11-18.md.

**Implementation still ahead (Phases 4–8):** private evidence intake/storage, verified
external enrollment/late-enrollment/Q04 release, prior no-certificate result workflow,
certificate/actual-exam verification, final annual/Silver credit, exceptional integrity/
separation/rehire consequences, mature reports/operations and remaining route details.
These are not falsely classified as external Google blockers. The current safe admission
path blocks evidence-dependent cases. Next implement the remaining Phase 4 evidence
and chronology vertical slice on these existing services, then Phase 5 exceptions and
Phase 6 assessment; preserve all current migrations and immutable audit.

---

# Historical Phase 2 checkpoint — superseded by current Phase 3 summary

2026-11-17. **Phase 0 complete; Phase 1 verified; Phase 2 local implementation verified, mandatory live Google UAT BLOCKED. Phase 2 is not declared complete.** All feasible identity, source-management and role-workspace work in `docs/codex/PHASE2_COMPLETION.md` is implemented. Academic domain services remain in Phases 3–7. This is not a production-readiness claim.

## Recovery and preservation

Recovered the interrupted working tree on `main`, including uncommitted/untracked source and migrations. The agent did not reset, discard or commit changes. A later repository checkpoint commit `034f71a` (testing backend) appeared during continuation; it is preserved, with subsequent fixes and documentation left as working-tree changes. The rejected Docker build at the interruption did not execute; subsequent authorized builds succeeded. Fixed the outstanding `apps/api/akus/startup.py` Ruff formatting issue. Existing Compose topology, PostgreSQL volume `akus-local_akus_pg`, source/audit data, prior migrations, specs and scan evidence are retained. Earlier progress is archived in `docs/qa/phase2a-build-progress.md` and `docs/codex/PHASE2_RECOVERY.md`.

## What works now

- **Institutional identity:** `apps/api/akus/identity/` implements real Google code exchange using discovery/JWKS, Authlib and joserfc; state/browser binding, nonce, S256 PKCE, RS256 signature, issuer/audience/time/verified-email/Workspace-domain validation; opaque server sessions, rotation, logout, HTTPS Secure cookies, CSRF and current source authorization. No configured client means CONFIGURATION REQUIRED. No provider tokens are stored or logged.
- **Controlled linking:** separate official email history, immutable issuer+subject links, observed verified-email history and sessions. No email-based role grants or automatic staff creation. Pending/denied/duplicate/disabled states, audited Admin reconciliation and exact old-link revocation are implemented. Operator-only first-Admin bootstrap and revocation are idempotent and require approved private roster facts; they never create a Google session.
- **Source administration:** `apps/api/akus/sources/` provides validated CSV/XLSX staging, normalized row previews, persistent errors, explicit atomic commit, deduplication and safe retries. Employment/rehire, department membership, institutional email, person and office corrections preserve before/after facts. Canonical subjects/aliases, departments and July–June years have usable setup pages. Original office facts are superseded, not rewritten.
- **Teaching:** create, filter, inspect, correct and void official assignments with effective intervals, term/year, provenance, conflict checks and immutable history. The timeline uses the first official date per employment episode and canonical subject; repeat teaching does not restart it, rehire does. IO-02 remains POLICY_PENDING; P-54 leap-day anniversary remains pending. No academic credit or violation is assessed.
- **Five distinct dashboards:** Faculty, DRC Head, HoD, Admin and Principal use real scoped source counts and working navigation. Faculty routing is DRC → HoD; DRC-own route is directly HoD. HoD/Principal applicant access is denied; Principal has global source reads without write authority. Academic links show actual NOT_IMPLEMENTED dependencies, never fake approval/quota/compliance outcomes.
- **Transactions/security:** effective permission checks on each request and after command locks; source/identity writes serialize consistently; PostgreSQL exclusion constraints prevent DRC/HoD overlap even across departments/concurrent writers. Immutable source revisions/audit, optimistic versions, command receipts and atomic import commits are tested.
- **Policy guide and recovery tooling:** searchable IO-02 and P-54 pending entries; spec inventory now has a read-only `--check` mode and preserves the later implementation policy register on regeneration. Canonical Admin route browser checks exercise alias corrections, year persistence and duplicate rejection.
- **Migrations:** preserved 0001–0003; added 0004 institutional identity, 0005 source management and 0006 verified-email/session history. Running app schema is `0006_identity_history`. Every migration also passed on new isolated `akus_phase2_completion_fresh_test`, followed by no drift and two successful demo seeds.

## Verified running result

Open **http://127.0.0.1:8080**. API docs: **http://127.0.0.1:8080/api/docs**. Existing Docker services are running; API/database healthy; migrate exited 0. Current environment is explicitly LOCAL/DEMO with no real linked identities. No new native services or second app were created.

Final gate: **109 PostgreSQL backend tests, 2 frontend tests, 28 Playwright tests passed**. Ruff lint/format (43 files), mypy (31 modules), ESLint, TypeScript, Prettier, production frontend build and migration drift checks passed. All four images (`api`, `migrate`, `worker`, `web`) rebuilt successfully. Responsive browser checks include 1440/1024/768/390/320 for foundation and 1440/390/320 for source/role pages; axe reported no violations in tested views. Desktop Admin, mobile DRC and teaching-history screenshots were visually inspected. Exact commands, repaired failures, fresh migration proof and limitations: `TEST_RESULTS.md`.

Demo: sign in as **Nila Shah · Admin** → Source imports → upload a LOCAL/DEMO roster → inspect preview → confirm commit → staff detail → Correct source record. Reference setup → add a synthetic canonical subject → Teaching allocations → record/correct assignment → inspect first-teaching timeline and history. Other fictional identities demonstrate scoped and read-only dashboards. See `docs/USER_MANUAL.md` for file columns and full steps.

## Remaining acceptance blockers and next steps

1. **External integration:** no approved Google Web OAuth client ID/secret, persisted private session key or actual voluntary Google login was available. All five named real-user cases remain BLOCKED / NOT VERIFIED. No successful real login is claimed.
2. **Authorized source facts:** the five email strings identify intended participants, not verified staff records. Approved staff keys, names, department/classification and effective appointment dates must be supplied privately before provisioning. Tracked `docs/fixtures/phase2-uat-roster.json` deliberately retains null facts. Use `docs/GOOGLE_OIDC_SETUP.md` to switch this same stack to a separate protected UAT database, bootstrap the approved Admin and complete real role tests. Do not insert real people into the demo dataset.
3. **Institutional policy:** IO-02 acceptance, P-54 leap day, Q51 multi-subject credit, role-transition consequences and existing-seat topic remapping remain pending. Corrections alter authoritative source facts only; they do not approve exemptions, waive obligations or decide historic academic consequences.
4. **Next planned phase:** Phase 3 canonical course/offerings, HoD primary-topic mappings and annual shared topic quotas, after the Phase 2 live-integration gate. Applications/review decisions and self-review transaction tests require Phase 4; evidence/annual/Silver assessment require Phase 6; historical separation consequences require Phase 7. No successful application submission exists yet.

## Persistent resume instructions

Read AGENTS, PHASE2_COMPLETION, BUILD_PHASES, this file, TEST_RESULTS, `docs/codex/PHASE2_CHECKLIST.md`, traceability and POLICY_GAPS before editing. Actual files remain the checkpoint. The agent created no commit; preserve the observed `034f71a` checkpoint and later working-tree changes. The entire 2,607-line master was read in bounded sections; 80 route contracts and Q01–Q50 remain inventoried and explicitly distinguish planned work from tested code. Master/blueprint hashes are unchanged. Do not restart Phase 2 or bypass Google to close the remaining acceptance gate.
