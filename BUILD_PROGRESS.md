# Full-system acceptance audit closed locally · 21 November 2026

The existing AKUS release is running at [the loopback origin](http://127.0.0.1:8080). The original PostgreSQL 16.16 cluster and volume remain at migration `0021_application_files`. The recovered 320-test checkpoint finished. The patched release passed 321 PostgreSQL tests, three web unit tests, 53 standard, four isolated and two supplemental browser journeys. All 22 discrepancy counters were zero on nine databases after the final browser writes. The release package covers all 80 blueprint pages and retains both the historical policies and their current amendments. [Audit checklist](docs/qa/FINAL_AUDIT_CHECKLIST.md) · [Requirements matrix](docs/qa/FINAL_REQUIREMENTS_MATRIX.md) · [Executed results](TEST_RESULTS.md)

This continuation repaired cross-department quota-transfer visibility for a holder of both an Admin grant and a department office, corrected the evidence workflow text and mobile layout, and applied vendor package fixes to the existing Compose services. Both new synthetic restores matched their source manifests. The optional clamd socket overlay is documented and its configuration validates. The five real Google accounts and private NPTEL evidence still await institutional UAT. Production release is **NO-GO**. Two critical DB image matches, other high advisories, deployed scanning, institutional verification and unratified decisions remain open. [Acceptance report](docs/qa/FINAL_ACCEPTANCE_REPORT.md) · [Security findings](docs/qa/SECURITY_REVIEW.md) · [Release owners and gates](docs/qa/RELEASE_READINESS_GATE.md)

Earlier checkpoints below preserve the order of execution.

## Full-system audit checkpoint

Post-patch tests passed 321 PostgreSQL cases with two dependency warnings and three frontend cases. Both fresh synthetic restores matched source manifests, including 66 application file revisions and 132 credential documents. The patched deployment retained its cluster and operational row counts. Remaining high/critical image advisories are documented release blockers. [Scan inventory](docs/qa/system-audit-image-advisories.md).

The quota-transfer list and case-detail services now enforce the academic office’s department even when the same person also has an Admin grant. The combined suite passed 321 backend and three frontend tests. Orca generated the expected control names and roles on both public pages. Trivy found additional image-level advisories outside the lockfiles. A targeted vendor package refresh is being evaluated.

Resumed audit on 21 November after the completed 320/3/53+4+2 checks. All 219 recorded input hashes match. Five stopped existing Docker services recovered on the original volume after a new private logical backup. Alembic reports head 0021 with no drift, the worker heartbeat is current, and all 22 counters are zero in seven databases. The earlier temporary snapshot directory was absent after the interruption. See docs/qa/system-audit-recovery-runtime.txt and docs/qa/system-audit-recovery-ledgers.txt.

The non-root release gate passed 320 PostgreSQL cases including the same-person distinct-course race and post-start rejection/withdrawal race. Playwright passed 53 standard, four isolated and two supplemental journeys. The record sweep reloaded 23 parameterized paths and the isolated Q44/Q47 journeys exercised the 24th. Both synthetic restores reproduced the audited evidence manifests. Final database reconciliation found zero discrepancies in all seven databases checked after the suites.

The focused search-to-evidence browser journey passed on the audited release. It opens the authorized file, quota movements, audit history and participation views after reload. The first combined backend run found the Faculty/DRC dashboard missing the newly required episode parameter. That shared query now binds the current episode. The first full browser run recorded a 30-second timeout during automated accessibility analysis; its assertions and timeout are unchanged for the full rerun. The patched npm lockfile has zero registry advisories (10 before), and all 45 Python release lookups returned no listed advisories.

2026-11-21 full-system audit baseline. Signed Phase 8 logs confirm 316 backend, 3 frontend, 52 standard and 4 isolated browser passes. The existing stack is ready at migration 0021. All 22 read-only counters were rerun on each of the eight databases. The private pre-change logical backup has a readable archive catalog. See docs/qa/system-audit-checkpoint.txt and docs/qa/system-audit-baseline.txt.

# Phase 8 passed local acceptance · 2026-11-21

The existing [local AKUS application](http://127.0.0.1:8080) runs on the original PostgreSQL volume at `0021_application_files`. The release passed 316 PostgreSQL tests, three frontend tests and 52 standard plus four isolated browser journeys. The complete route matcher covers all 80 blueprint paths. The 22 read-only discrepancy checks returned zero in the operational database, five test databases and both synthetic restores. [Acceptance checklist](docs/codex/PHASE8_CHECKLIST.md) · [Executed checks](TEST_RESULTS.md)

The interrupted build and startup logs recorded successful image builds and migration. The later combined check had failed because repeated scans generated duplicate vacant HoD notices. The reviewer and delivery services now preserve the office observation and use the effective appointment as the delivery address. The release also closes the draft and submitted application evidence pages. Applicants can attach a private PDF, replace it with an immutable revision, or remove it from a draft. Submission records the exact revision IDs in the reservation transaction. Downloads enforce current authorization, scan status and private cache headers. The user manual includes a reproducible walkthrough.

The next acceptance work requires institutional input. The five live Google journeys need approved OAuth configuration, authorized roster and appointments, and voluntary sign-in. Production scanner acceptance, private provider verification and deployment-specific recovery remain open. Decisions about IO-02, Q51, retroactive mapping and a final remedy for a blocked quota transfer remain in [the policy register](POLICY_GAPS.md). Resume from the current uncommitted working tree, [Phase 8 checklist](docs/codex/PHASE8_CHECKLIST.md) and [operator runbook](docs/OPERATIONAL_RUNBOOK.md).

## Earlier checkpoints

## Phase 8 recovery · 2026-11-21

The final backend passed 316 tests. The four file tests also passed on the database migrated from empty. Both synthetic restores returned zero for every one of the 22 discrepancy counters, including attachment-to-audit and submission-to-revision integrity. The first full browser run passed 52; the isolated run passed four. Final-image browser verification is running.

The retained stack migrated to `0021_application_files` and reported ready with a current worker heartbeat. On the upgraded release test DB, all 315 collected backend tests passed. Prettier subsequently flagged the new browser test; it was formatted. The new clean-file delivery test and complete suite are running on a fresh database. A separate logical restore reproduced 9,053 audit events, 565 quota movements and all seven application attachment revisions.

The release and signed Compose builds completed and the migration exited 0. The release browser run had two failures during sign-in navigation and lazy route loading. The signed browser rerun passed all 51 journeys. The signed combined check then exposed a duplicate vacant HoD alert. Delivery now uses the appointment recorded by the coverage check, and comparison with older alerts ignores delivery-only metadata. The original vacancy regression and private delivery replay test both passed in Docker. See [focused results](docs/qa/phase8-resumed-alert.txt). The acceptance run for the new application attachment workflow is in progress.

Phase 8 recovery verified the retained Phase 7 checkpoint on main at de5844c, including its uncommitted changes. Saved results show 272 backend, two frontend, 42 standard and four isolated browser passes. All 18 discrepancy checks were zero on each of four databases. The live API and database are healthy at 0019_employment_sessions on the original volume.

Phase 8 milestone 2 · Provider refresh jobs, ambiguity flags, real public preview and 80 explicit route matches exercised. Final role, historical reporting, Docker and browser checks in progress.

Phase 8 milestone 1 · The workspace registers, personal inbox and job retry commands now run on isolated PostgreSQL migration 0020_workspace. All 29 focused API tests passed. Browser and release acceptance pending.

# Phase 7 local acceptance passed

The existing [AKUS local application](http://127.0.0.1:8080) is running at `0019_employment_sessions` on the original `akus-local_akus_pg` volume. The final Compose build, start, combined test gate, both browser suites and read-only reconciliation completed successfully. [Checklist](docs/codex/PHASE7_CHECKLIST.md) · [Test evidence](TEST_RESULTS.md)

Admins can preview an episode's applications, quota occupancy, subject deadlines and offices, and record rehire with its initial home department in one audited transaction. Faculty and DRC Head can inspect their own earlier episodes, closure decisions, original subject status and linked annual/Silver assessments. Rehire requires fresh sign-in. A new session cannot use ordinary applicant commands to change the earlier episode. Existing department/institution report permissions still apply at read time.

Historical registers now use the workforce and staff names recorded by the requested cutoff. A delayed permanent order freezes the teaching revision then known. Later confirmed evidence and corrections append observations. Existing Q43–Q47 final decisions, quotas and the original separation snapshot retain their histories. The migration preserves identity links and leaves unattributable legacy sessions subject to fresh authentication.

**Verified** — 272 PostgreSQL tests, two frontend tests, 42 standard browser journeys and four additional isolated journeys. All 18 discrepancy counts were zero in the operational database and each of three test databases. The six new backend tests cover mixed closure/rehire and personal-history authorization, historical roster selection, concurrent final approval and HR action, concurrent credential and integrity review, institutional-session continuity, and delayed HR recording. [Demo steps](docs/USER_MANUAL.md) · [Traceability](docs/traceability.md)

Real Google acceptance, live certificate-provider verification, malware scanning and unratified institutional decisions remain open. Phase 8 is the next approved phase for route coverage and UI/QA. [Policy gaps](POLICY_GAPS.md) · [Build plan](docs/codex/BUILD_PHASES.md)

## Earlier checkpoints

Phase 7 milestone 2 passed. The 271-test Docker check exited 0 with four dependency warnings and two Vitest passes. It includes HR versus final HoD approval, integrity versus certificate review, and the institutional-session rehire test with a local signing key. All 42 full Playwright journeys passed on the first Phase 7 build. The final revision also replays teaching revisions for delayed permanent orders and rejects writes to an earlier episode after rehire. Verify that revision with phase7-acceptance.txt, phase7-final-browser.txt and phase7-isolated-browser.txt.

Phase 7 milestone 1 passed. The combined Docker gate exited 0 with 268 PostgreSQL tests, four deprecation warnings, two Vitest passes, clean static checks, a successful Vite build and zero migration drift on a fresh test database. Mixed Q45/Q47 closures, repeated processing, atomic rehire, stale-session rejection and historical roster filters passed. The original Compose database upgraded to 0019_employment_sessions. See docs/qa/phase7-first-checks.txt and docs/qa/phase7-start.txt. Final browser and concurrent-decision gates follow.

Phase 7 recovery. Main at de5844c contains Phase 6. Read-only checks confirmed healthy API and database at 0018_exam_evidence on the original volume. The saved gate records 266 backend, two frontend and 40 full browser passes plus four isolated journeys. All 13 saved discrepancy counters were zero in each of four databases. Phase 7 work and outstanding gates are tracked in docs/codex/PHASE7_CHECKLIST.md.

# Phase 6 local acceptance passed · 2026-11-20

The running [AKUS demo](http://127.0.0.1:8080) serves the certificate library, annual NPTEL compliance and subject-wise Silver reports on the original PostgreSQL volume. The live API reported ready at migration head `0018_exam_evidence`. The worker heartbeat, frontend response and Alembic drift check passed. [Runtime evidence](docs/qa/phase6-signed-health.txt)

Resumed the existing Phase 6 checkout. The interrupted browser suite had already finished. Fixed the Prettier failure in its test file and three certificate-history defects. A later claim or independently established exam now reopens the prior-outcome check for repeat admission. A score-only correction preserves an independent subject-relevance ruling across separation. Historical reports use the actual time of an integrity notice and retain a formal invalidation after the hold closes. The regression tests preserve the earlier as-of view as well as the later decision.

The combined Docker gate exited 0 with **266 backend tests and 2 frontend tests passing**. The recovered full browser suite passed **40 journeys**, two affected journeys passed again, and the final isolated suite passed **4 journeys**. All 13 quota and compliance discrepancy counts were zero on the operational database and each of three test databases. [Test results](TEST_RESULTS.md) · [Phase 6 checklist](docs/codex/PHASE6_CHECKLIST.md)

To exercise the demo, open **Certificate library** and **Compliance reports** from the local Faculty or DRC Head dashboard. HoD and Principal have department and institution report registers respectively. Genuine institutional evidence decisions still require a documented, active reviewer appointment. Live Google sign-in awaits approved credentials, staff and office records, and voluntary account-holder participation. Unratified decisions remain policy-pending. The next approved phase is Phase 7, employment exits and historical correctness. [User manual](docs/USER_MANUAL.md) · [Policy register](POLICY_GAPS.md)

## Earlier checkpoints

Phase 6 recovery milestone 7. The 265-test gate, frontend build, two affected Playwright journeys and four isolated case journeys passed. A final historical-report check now distinguishes a resolved integrity hold from formal invalidation at the report knowledge cutoff. The final acceptance evidence is phase6-signed-checks.txt, phase6-signed-health.txt and phase6-acceptance-ledgers.txt.

Phase 6 recovery milestone 6. Started the stopped original containers without recreation. The retained volume is mounted and the live API reported ready at 0018 with no drift. The recovered gate passed 263 backend tests, Vitest 2, formatting and Vite. Review added regressions for later evidence after a no-certificate decision, and a separated participant’s original subject decision across score-only corrections. Final validation is phase6-acceptance.txt plus read-only database reconciliation.

Phase 6 recovery milestone 5. The final browser log completed with 40 passes and the isolated suite with four passes. The combined script completed its 263 backend tests but stopped at Prettier before Vitest/build. A whitespace-only correction to e2e/phase6.spec.ts passes the targeted format check. Next command is AKUS_TEST_DATABASE_NAME=akus_phase6_release_test scripts/check-docker.sh; retain phase6-recovery-gate.txt, runtime and read-only reconciliation evidence.

Phase 6 milestone 4. Revision 0018 upgraded the fresh release test database with no drift; 258 PostgreSQL tests passed. The existing demo stack upgraded in place and the API became healthy. The compiled suite passed both new journeys and 37 earlier journeys. Its remaining failure exposed a desktop sidebar that could push Sign out below the viewport. The sidebar now scrolls. The isolated fixture parser also accepts the pytest progress dot. The department/institution registers, historical cutoff filter and extended separation/race tests await the final rerun. See docs/qa/phase6-0018-checks.txt and phase6-browser.txt.

Phase 6 milestone 3. Twelve targeted PostgreSQL tests passed in 6.62 seconds (phase6-credential-recheck.txt), including competing verifications, repeated report captures, revocation, archived observations, private access and threshold/deadline checks. The first targeted invocation used the wrong public origin and was denied; no origin guard changed. Added 0018_exam_evidence and June/July, Q51, integrity and exam-only regressions after that run. Next run is phase6-0018-checks.txt.

Phase 6 milestone 2. The first isolated Docker run upgraded through 0017 with no drift and passed all 242 existing PostgreSQL tests (111.52s, 3 warnings). ESLint found a now-removed unused route import. Credential library/forms, scoped annual/Silver reports and new database tests are in the checkout, pending acceptance. See docs/qa/phase6-first-checks.txt.

Phase 6 milestone 1. Added migration 0017_compliance, appointment-scoped credential commands, private PDF quarantine, episode assessments and stored observations. Local Ruff passed and mypy passed across 69 sources. PostgreSQL and browser acceptance remain unverified. Next command: AKUS_TEST_DATABASE_NAME=akus_phase6_acceptance_test scripts/check-docker.sh.

## Phase 6 · 2026-11-20

Phase 6 recovery confirmed main at 4f54152 and five running Docker services. Work starts with the active certificate register, followed by episode assessments and signed-in pages. See docs/codex/PHASE6_CHECKLIST.md.

# Phase 5 local acceptance passed · 2026-11-19

The running application is available at http://127.0.0.1:8080 on the original akus-local_akus_pg volume. API readiness reports PostgreSQL connected at 0016_archived_obligations. The API, worker, frontend and proxy are running. The existing migration job exited successfully. The repository remains on main; the earlier uncommitted implementation is preserved.

**Verified** — 242 PostgreSQL tests, 2 frontend tests, 38 standard Playwright journeys and 3 additional isolated browser submissions. The latter exercise Q47 closure, historical certificate verification with as-of replay, and Q44 closure from a late date-only enrollment document. Ruff, mypy, frontend lint/format/typecheck, production builds and live migration drift passed. Live reconciliation covered 28 transfer movements with zero inconsistent pools, invalid transfer pairs, per-application balance mismatches, terminal release mismatches, exceptional decision mismatches or stale terminal separation tasks. The same counters were zero on both retained test databases.

The final fixes preserve the former HoD's loss of access, link a superseded separation task to an independent integrity invalidation, retain source date precision, and scope worker wakeups to actual capacity waiters. Case history, denied writes and replay are tested. See [the Phase 5 checklist](docs/codex/PHASE5_CHECKLIST.md) and [verification evidence](TEST_RESULTS.md).

**Pending** — Real Google sign-in requires approved OAuth configuration, authoritative staff records and voluntary account-holder participation. Policies for retroactive topic moves, blocked-transfer final disposition, multiple-subject reuse and teaching acceptance remain open. General verification and integrity adjudication require documented authority. The next approved phase is Phase 6 evidence and compliance.

---

# Phase 4 local acceptance passed · 2026-11-19

The Docker application is available at http://127.0.0.1:8080. Recovered the uncommitted Phase 4 work on main at 4743023. The existing database and original akus-local_akus_pg volume were retained. Migrations 0011_application_workflow and 0012_prior_outcomes are applied. No downgrade, volume deletion or database reset occurred.

Faculty can resume versioned drafts, submit against an annual department/topic pool and follow DRC → HoD review. DRC applicants route directly to the current distinct HoD. Reviewers can resolve enrollment chronology at the source's actual precision. A pending seat survives the enrollment deadline. Late final approval requires verified enrollment after submission or a documented official extension. An enrolled applicant can request pre-start withdrawal. A current HoD decision releases the currently charged seat once. Post-start voluntary withdrawal retains it.

Faculty and DRC applicants can report a prior offering from the catalog and revise the evidence. The HoD verification inbox supports search, sorting and case deep links. Independent findings bind the permanent person, exact run, canonical course, source digest and office. Unresolved outcomes block reservation. A verified unsuccessful attempt permits fresh consideration. A valid certificate bars future repeats. Corrections preserve history and an affected newer approval enters a recognition hold with its counted seat retained. A submitted snapshot identifies the prior findings used at admission.

The final PostgreSQL suite passed 210 tests. Both frontend unit tests and all 36 browser tests passed, including responsive and accessibility checks. Docker, migration drift, worker heartbeat, API readiness and live quota reconciliation passed. The repaired catalog search persists across provider tabs. Detailed evidence and known warnings are in TEST_RESULTS.md. Demo steps and boundaries are in docs/codex/PHASE4_CHECKLIST.md.

Next approved work is Phase 5 authority rotation, deadline reminders and exceptional-case processing. Independent integrity disposition and emerging-technology authority still require institutional direction. Private document storage, actual examination and annual/Silver assessment belong to Phase 6. Live Google UAT remains externally blocked. The current runtime reports google_enabled=false and zero external identity links. The approved OAuth configuration, institutional records and five voluntary account-holder sign-ins remain required.

---

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

Phase 5 separation milestone: seven isolated PostgreSQL tests passed after separating committed fictional staff fixtures from the baseline seed database. Historical assessments and full browser/runtime acceptance are in progress.

The historical certificate and office coverage slice passed the 0014 gate (221 PostgreSQL tests, 2 Vitest). Docker rebuilt all four requested images and the original database migrated forward. The new case pages are available on the existing local web port.

The 0015 gate covered 234 passing PostgreSQL tests, 2 Vitest tests, 38 Playwright tests against the normal Docker stack and 2 isolated Playwright tests of actual Q47 and retrospective certificate submissions. A final policy review added 0016, an additive archive of previously adjudicated obligations. It distinguishes genuinely confirmed historical obligations from teaching sources subject to IO-02. The final tests are running against akus_phase5_acceptance_test.

The interrupted final check completed with 235 passes and one failure in the office rotation test. The recovered gate passed after testing the former HoD's exact loss of dossier access and the Admin/Principal academic-write denials. Regressions now cover concurrent separation/integrity dispositions and late enrollment documents with date-only precision. The final acceptance evidence is being collected in docs/qa/phase5-final-acceptance*.txt.

On the retained demo database, browser repetition exposed two fixture-volume effects. A Principal directory test assumed the subjects were on the first page, and a quota publication enqueued rechecks for unrelated enrollment and integrity cases. The directory journey now searches by exact staff name. Capacity changes wake the affected transfer waiters and the worker drains successive full batches without the idle delay. Independent transactions exercise publication racing a missing destination. The original browser timeout and outcome assertions are preserved.

### Post-audit remediation — database image and recovery, 2026-11-21

Restored a fresh private logical archive into a network-isolated PostgreSQL 16 candidate on tmpfs. The original and restored audit, ledger and evidence manifests matched and all 22 restored discrepancy counters were zero. Rolled out the rebuilt database image on the existing named volume. The cluster identifier remained 7708476577220165670 and the migration remained 0021_application_files. Trivy now reports one critical in the database image. The rebuilt gosu 1.20 uses Go 1.27.4. Debian's libxml2 critical remains open. See [restore evidence](docs/qa/remediation-candidate-restore.txt) and [release blockers](docs/qa/RELEASE_BLOCKERS.md).

### Post-audit remediation — private evidence and identity

Activated the private ClamAV service and FreshClam on the local stack. Verified real signature detection, unavailable-socket quarantine, safe retry, private clean delivery, denied unrelated access and immutable certificate re-submission. Each new attachment audit or certificate assertion records its clean scanner version. Certificate download uses the selected assertion revision. Added fresh-signature and framing checks and a server guard against authenticating person-specific findings with known public course previews. Google discovery and public keys resolved. All five live sign-ins still require institutional action. [Scanner acceptance](docs/qa/remediation-final-scanner.txt) · [Public integration evidence](docs/qa/remediation-integrations.txt)

### Post-audit remediation — release image qualification

Rebuilt the stock Caddy command with patched dependencies, compared its full module list and validated forwarding and the login route. All six release images and ClamAV have matching-database Trivy reports. The database has one critical and 125 high matches. API, migrator and worker have 50 high each. Web and proxy retain one high each. ClamAV has zero matches after the supported Alpine libxml2 update. No remaining high/critical match has a scanner-listed fix. The institutional release gate stays closed. [Image IDs and counts](docs/qa/remediation-image-scans.md) · [Owner register](docs/qa/RELEASE_BLOCKERS.md)

### Post-audit final acceptance checkpoint — 2026-11-21

All local remediation acceptance suites finished. 331 backend, two additional real-engine, three frontend and 60 Playwright tests passed. All 242 discrepancy readings were zero across eleven databases. The local API/DB/scanner are healthy, the worker heartbeat is fresh and the original operational counts match preflight. The release remains NO-GO pending the critical Debian libxml2 match, remaining high package matches, live institutional sign-ins (0/5), authentic private provider evidence, production controls and governance. No historical migrations or institutional appointments were changed.

Resume from the [remediation report](docs/qa/POST_AUDIT_REMEDIATION_REPORT.md) and [owner register](docs/qa/RELEASE_BLOCKERS.md). Use both compose.yaml and compose.scanner.yaml for scanner-enabled changes. The original database backup and full raw scans remain in the ignored private remediation directory. Keep all existing volumes and working files. [Test results](TEST_RESULTS.md) · [Next institutional actions](docs/qa/EXTERNAL_DEPENDENCIES_AND_POLICIES.md)
