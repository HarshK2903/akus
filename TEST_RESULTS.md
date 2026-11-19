# Phase 5 verified results · 2026-11-19

| Gate | Observed result | Evidence under docs/qa |
|---|---|---|
| Recovery | 0016 upgrade had completed. The interrupted gate finished with 235 passed and one failed assertion about the former HoD's exact denial. The corrected targeted rotation test passed. | phase5-0016-final-checks.txt, phase5-0016-start.txt, phase5-office-rotation-recovery.txt |
| Final backend and concurrency | `AKUS_TEST_DATABASE_NAME=akus_phase5_acceptance_test scripts/check-docker.sh` passed all 242 PostgreSQL tests in 115.50s, with 3 deprecation warnings. Ruff check/format passed for 89 Python files. Mypy passed on 62 source files. Alembic detected no schema drift. | phase5-verified-checks.txt |
| Final frontend | The combined run identified a Prettier issue in the edited browser test. After formatting, the separate final run passed ESLint, TypeScript including isolated browser tests, Prettier, 2 Vitest tests and the Vite production build. | phase5-verified-frontend.txt |
| Docker images and startup | API, worker, migrate and web built. Runtime services refreshed without replacing PostgreSQL. Original volume creation time retained. Running source hashes matched the checkout. | phase5-verified-build.txt, phase5-verified-start.txt, phase5-verified-health.txt |
| Compiled frontend/browser | 38/38 Playwright tests passed. The 20-second transfer assertion and current-pool withdrawal passed on the retained demo data. The new case routes had no axe violations or horizontal overflow at 320, 390 and 1440 px. | phase5-browser-acceptance.txt, phase5-integrity-320.png, phase5-separation-390.png |
| Isolated authenticated browser | 3/3 passed using the same compiled UI, a separate test database, normal demo sign-in and actual guarded writes. Saved a Q47 closure, verified an archived certificate and reconstructed the earlier report, and saved a Q44 day-precision enrollment with no exact time. | phase5-browser-case-acceptance.txt, phase5-q47-detail-320.png |
| Read-only consistency | `scripts/verify-quota.sql` reported zero on all six mismatch counters in all three databases. The operational DB contained 28 transfer movements. The retained departure DB included 122 separated and 10 invalidated applications. The standard concurrency DB contained 87 transfer movements. | phase5-verified-health.txt, phase5-verified-departure-ledger.txt, phase5-verified-concurrency-ledger.txt |
| Security and traceability | Anonymous/Faculty list denials and CSRF plus foreign-Origin denials on six write routes passed. The local pattern scan found zero matches in 107 source/config files. The spec inventory verified 80 target routes, 50 historic policies and 27 policy entries. | phase5-verified-authorization.txt, phase5-verified-security-scan.md, phase5-verified-spec.txt |

The live API reported ready, the frontend returned HTTP 200 and the worker had a recent heartbeat. Google sign-in was disabled with zero institutional identity links. Synthetic case appointments and historical obligation rulings were confined to isolated test databases. Institutional account-holder sign-ins are still outstanding.

The backend warnings concern FastAPI/Starlette TestClient, Authlib’s HTTPX integration and Alembic path configuration. Vite emitted its bundle-size advisory. Earlier logs preserve intermediate failures, including directory first-page assumptions, a stale employment-page selector and unrelated quota-worker wakeups. The corrected employment workflow waits for the destination heading and verifies the exact dated row inside its episode register.

---

# Phase 4 final local verification · 2026-11-19

| Executed gate | Observed result | Evidence under docs/qa |
|---|---|---|
| Recovered original Phase 4 workflow and catalog check | 7 affected browser journeys passed after the draft route and search-filter repairs | phase4-workflow-browser-pass.txt |
| First 0012 full gate on existing isolated test DB | 204 backend tests passed, mypy passed on 55 modules and Alembic found no schema drift | phase4-outcome-first-checks.txt |
| Extension and correction race checks | 206 backend tests passed. Prettier reported the browser test under edit. Formatted the file and repeated the full gate | phase4-recovery-checks.txt |
| Final scripts/check-docker.sh using akus_phase4_forward_test | **210 backend passed, 2 warnings, 60.63 seconds**. Ruff check and format passed (77 files), mypy passed (55 modules). Forward upgrade and drift checks passed. ESLint, TypeScript, Prettier, **2 Vitest tests** and Vite production build passed | phase4-final-checks.txt |
| docker compose build api migrate worker web, then up -d | Four images built, migration exited 0, API and DB healthy, worker/web/proxy running on existing volume | phase4-final-build.txt, phase4-final-start.txt, phase4-final-health.txt |
| Full Playwright against compiled Docker/Caddy app | **36 passed (1.3 minutes)** including the filtered HoD prior-result inbox, immutable evidence revisions, later correction, enrollment findings, current-pool withdrawal, mobile layouts and axe checks | phase4-final-browser.txt, phase4-prior-outcome-390.png, phase4-participation-{320,390,1440}.png |
| Live read-only SQL, HTTP and Alembic | 0012_prior_outcomes at head, no drift, 0 inconsistent pools, 0 invalid transfer pairs, worker heartbeat under one second old at observation. Frontend HTTP 200 and readiness reported connected | phase4-final-health.txt |
| Requirements inventory and traceability | Master and embedded blueprint retained. Inventory verified 80 pages, 50 historic policies and 27 policy-register entries | scripts/spec_inventory.py --check, docs/traceability.md, docs/POLICY_TEST_TRACEABILITY.md |

The PostgreSQL tests exercise independent transactions for last-seat admission, concurrent canonical applications, source changes, withdrawal versus transfer, receipt replay and prior certificate correction versus final approval. A correction that wins first prevents approval. A correction that arrives after approval opens an integrity hold and retains the seat. Pre-start withdrawn and rejected applications can be followed by independent eligible submissions. Distinct courses can remain active concurrently. Source evidence on another run cannot be hidden by starting a new draft.

Backend warnings came from the installed Starlette/Authlib HTTP client deprecations. Vite reported a 520 kB minified bundle warning. Browser tests use labelled local accounts, synthetic offerings and documentary references. Real Google sign-in remains unverified. General evidence and final integrity authority remain subject to institutional policy.

Reproduce with `AKUS_TEST_DATABASE_NAME=akus_phase4_forward_test scripts/check-docker.sh`, then `AKUS_E2E_URL=http://127.0.0.1:8080 PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e` on the existing Compose installation. Repeated browser runs add labelled demo data. Earlier failure logs remain in docs/qa.

---

# Observed verification — Phase 3 recovery, 2026-11-18

**Local catalog/topic/quota + expanded admission/reschedule acceptance passed.**
Live Google and five real account-holder UATs remain BLOCKED/NOT VERIFIED. Full
AKUS evidence/compliance, all 80 page contracts and production readiness are not claimed.
The old /tmp interruption log was absent after restart; the prior 173/1 result is a
reported checkpoint, not a newly read traceback. New durable evidence is below.

| Executed command/check | Observed result | Evidence under docs/qa |
|---|---|---|
| Original withdrawal-vs-transfer test, five pre-fix repetitions | All 5 passed; scheduler ordering did not force the bug | phase3-withdrawal-reproduction.txt |
| Added deterministic withdrawal-before-source-acceptance regression, pre-fix | FAILED 423 VERIFIED_COMMENCEMENT_REQUIRED vs required 200; full traceback retained | phase3-withdrawal-ordered-failure.txt |
| Docker pytest test_admission.py after commencement fix | **45 passed**, 2 dependency warnings, 22.84s; original race retained plus two new ordering/source tests | phase3-admission-recovery.txt |
| First full scripts/check-docker.sh | **176 passed**, then frontend gates passed | phase3-checks-before-case-closure.txt |
| Final scripts/check-docker.sh after terminal-case closure | **177 passed, 2 warnings, 43.81s**; Ruff lint, format **66 files**, mypy **48 modules**, Alembic head/drift; ESLint/TypeScript/Prettier, **2 Vitest tests**, Vite production build passed | phase3-final-checks.txt |
| Frontend checks after visual corrections | lint/types/format, **2 Vitest tests**, production build passed; final formatting check passed | tool output; phase3-final-frontend-format.txt; phase3-web-build-final.txt |
| docker compose build api migrate worker web; up -d | PASS all four existing images; final web rebuild after copy/layout correction also passed | phase3-build.txt, phase3-start.txt, phase3-web-build-final.txt, phase3-web-start-final.txt |
| Fresh isolated akus_phase3_recovery_fresh_test: upgrade head/current/check, startup twice | **0010_personal_schedule**, no new upgrade operations; both fictional seeds succeeded. New database retained | phase3-fresh-migrations.txt |
| First full browser run | **32 passed / 1 failed**: legacy employment-date locator matched employment and department tables. Corrected scope; assertions retained | phase3-browser-initial.txt, phase3-browser-employment-selector.md |
| Full Playwright after repair, compiled Docker app | **33 passed (1.1m)**; original 28 plus 5 Phase 3 flows, responsive/axe evidence | phase3-browser.txt |
| Final affected system-page Playwright after copy-only correction | **12 passed (10.4s)** including 1440/1024/768/390/320 accessibility, navigation and recovery | phase3-system-browser-final.txt |
| Existing database current/check, Docker health and volume | **0010_personal_schedule**, no drift; API/DB healthy; worker/web/proxy running; migrate exit 0; original volume created 2026-11-16 retained | phase3-health.txt |
| Live quota aggregate integrity | **0 inconsistent pools, 0 invalid transfer pairs**; every observed job DONE (62 at check), worker heartbeat fresh | phase3-health.txt |
| HTTP frontend, ready, auth config and authenticated foundation | **HTTP 200**, ready/connected/0010, worker running; demo true, Google false. NPTEL participation verification remains not connected; public metadata is a separate working adapter | phase3-http-health.txt |
| Real authenticated local Admin → public NPTEL metadata fetch | **OBSERVED / OFFICIAL_HTTPS**, noc26_cs98, normalized title/dates/categories, immutable digest; left AWAITING_SOURCE_ACCEPTANCE | phase3-live-provider.txt |
| spec_inventory --check; traceability generator; py_compile; git diff --check | PASS: **2,607 lines, 80 routes, 50 historic policy rows** retained; current policy amendments separated | phase3-spec-check.txt; root/generated documents |
| Limited source pattern scan | **90 files, 0 matching files**; earlier reports retained, not comprehensive security certification | phase3-secret-scan-final.md |

Browser command: `AKUS_E2E_URL=http://127.0.0.1:8080 PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e`.
Backend gates use real PostgreSQL in isolated `akus_completion_test`; no SQLite,
reset or volume deletion. Browser fixtures use clearly fictional identities and source
records in the demo database; records/audit remain after tests. Migrations 0001–0010
were not reset or downgraded. New changes required no replacement of applied history.

## What the new tests establish

The original failing concurrency test is unchanged. Exam-date-only conflicts no longer
make withdrawal's outcome depend on source-acceptance order. Withdrawal keeps accepted
commencement evidence fresh/consistent, serializes on offering/application, reads the
authoritative current allocation and releases once; retry cannot release twice.
A conflicting commencement still blocks. The pre-fix deterministic reproduction
established a precondition race, not an observed double-decrement; count, ledger,
capacity and idempotency assertions remain intact.

Other admission/catalog cases cover exact canonical/offering identity, approved topic
and quota publication, full/shared pool, last-seat and mapping-revision races, cap
reductions, immutable submission and ledger, two-stage/direct-HoD review, actor scope,
CSRF, exempt applicants, stale/unavailable sources, same-year/older/repeated/roundtrip
reschedules, last target seat, current-pool rejection/withdrawal, retained closure,
as-of/privacy and office transitions. Manual personal schedule tests bind current HoD,
exact applicant/offering and archived evidence, including different years for two
people in one run. Released work closes without authenticating a pending claim.

Browser Phase 3 journeys: catalog→mapping request→HoD mapping→annual publication;
Faculty draft→DRC→HoD→blocked transfer→destination publication→worker transfer→current
pool withdrawal; DRC-own direct HoD/no self-review; personal claim→independent HoD
verification for one person only; Admin source/metadata navigation with Faculty denied.
Case deep-link refresh and target quota navigation are exercised. Axe and responsive
screenshots cover 1440/390/320 Phase 3 pages; prior foundation also 1024/768. Actual
screenshots were inspected and checkbox sizing/stale copy corrected. Screenshots:
phase3-{quota,application}-{1440,390,320}.png.

## Data, source and verification limits

Point-in-time live DB at final health evidence: **28 people, 195 source revisions,
915 audit events, 14 applications, 29 ledger entries, 3 personal schedule revisions,
0 external identity links**. Later browser checks add labeled synthetic records; these
counts are observations, not invariant expected totals. Original volume is retained.

Public source fetch at 2026-11-18T13:44:45Z returned AI for Earth Observation,
12 weeks, categories COMP_SCI_ENGG/Domain_15, scheduled exam 2026-10-16 and historical
2026 dates. Digest `6779ee9e5b883a2890bb1b20815603818137d94dccc1ab65816b2796fe361824`.
This is real public metadata evidence, not provider availability monitoring, current
eligibility, external enrollment, certificate or real Google login. Manual HoD findings
in tests are synthetic and labeled; no real faculty document was authenticated here.

Two backend warnings are upstream Starlette/Authlib httpx deprecations with locked
working dependencies; no tests were skipped to hide them. Browser NO_COLOR/FORCE_COLOR
warnings are non-failing tooling warnings. Remote CI and production deployment not run.

Master SHA-256 `f3a8fcfbef034fe76da05c6331427fa6d846b2e4c02f073934550de00e276e36`;
blueprint `2c349d6ddb9fbaa61c5689aab524b830d89ec854dea61f27ddc6cc7dd9dd51c7`, unchanged.
Real Google prerequisites remain client/private key, approved roster/appointments and
five voluntary sign-ins; see docs/GOOGLE_OIDC_SETUP.md. Remaining institutional policy
and later implementation boundaries: POLICY_GAPS.md and docs/codex/PHASE3_CHECKLIST.md.

---

# Historical verification — Phase 2 continuation, 2026-11-17

**Local Phase 2 implementation verified. Mandatory live Google UAT BLOCKED; Phase 2 is not declared complete.**
This section supersedes current-state statements in the retained Phase 2A/Phase 1
history below. Current browser http://127.0.0.1:8080; API docs at the same origin
/api/docs. Existing Docker services/volume are retained; no second native stack was
started. All current application records remain conspicuously LOCAL/DEMO.

| Actual command / check | Observed result and evidence |
|---|---|
| `docker compose build api migrate worker web` | PASS, all four images built. The earlier denied attempt did not execute; this later authorized build did. docs/qa/phase2-completion-build.txt |
| `docker compose up -d`; `docker compose config -q`; `docker compose ps -a` | PASS. API and DB healthy, web/proxy/worker running, migrate exited 0. docs/qa/phase2-completion-start.txt |
| `scripts/check-docker.sh` | PASS. Ruff lint/format **43 files**, mypy **31 modules**, migrations/drift, **109 PostgreSQL tests passed (12.28s)**, ESLint, TypeScript, Prettier, **2 Vitest tests**, production Vite build. docs/qa/phase2-completion-checks.txt |
| Isolated fresh DB: `alembic upgrade head`, `current`, `check`, startup seed twice inside existing API image | PASS on newly created `akus_phase2_completion_fresh_test`: **0006_identity_history (head)**, no new upgrade operations, both seed calls succeeded. Database retained. docs/qa/phase2-completion-fresh-migrations.txt |
| `AKUS_E2E_URL=http://127.0.0.1:8080 PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e` | **28 passed (48.9s)** on compiled Docker/Caddy/FastAPI/PostgreSQL. Includes original 20 equivalents plus eight Phase 2 tests. docs/qa/phase2-completion-browser.txt |
| Proxy HTTP checks with curl | Frontend **HTTP 200**; readiness **ready / connected / 0006_identity_history**; auth config **demo_enabled:true, google_enabled:false** |
| Existing app DB source/schema inspection | Head **0006_identity_history**; snapshot during final browser run: **18 people, 107 immutable source revisions, 327 audit events, 0 institutional identity links**. Later browser actions add synthetic facts; these are point-in-time counts, not fixed expectations |
| Existing Docker volume inspection | Original **akus-local_akus_pg**, created 2026-11-16T00:36:02+05:30, retained. No down -v, reset, prune or volume deletion |
| `python3 scripts/spec_inventory.py --check`; regeneration-preservation assertion | PASS: **2,607 lines, 80 routes, 50 historical policies, 27 original register entries**; embedded blueprint exact. Regeneration preserved the complete later policy continuation including IO-02 |
| `python3 scripts/traceability.py` | PASS: 80 target route rows, 50 policy rows, current local evidence separated from planned domain tests |
| `python3 scripts/scan-source.py --report docs/qa/phase2-completion-secret-scan.md` | PASS: **68 source/config files, zero matches** for limited private-key/GitHub/AWS patterns. Earlier scan reports retained; not comprehensive security certification |
| `git diff --check`; Python compile of inventory/traceability tooling | PASS |
| Specification SHA-256 | Master **f3a8fcfbef034fe76da05c6331427fa6d846b2e4c02f073934550de00e276e36**, blueprint **2c349d6ddb9fbaa61c5689aab524b830d89ec854dea61f27ddc6cc7dd9dd51c7**; unchanged |

## What the tests prove

The original 45 backend tests remain included. Added identity/source coverage brings
the total to 109, not 109 additional tests. Tests use an isolated database ending
_test and real PostgreSQL transactions/constraints. No SQLite substitute or real
account impersonation is used.

Identity tests exercise signed tokens with locally generated RSA keys, wrong signature,
issuer/audience/hd/nonce/time/unverified email/missing claims; real Authlib code-exchange
and JWKS paths against isolated HTTP responses; one-use expiring browser-bound state,
PKCE, redirect allowlist, consent/error paths, session rotation/expiry/logout/CSRF,
HTTPS-cookie/config boundaries, active source authorization, disabled/separated staff,
immutable subject/change-email behavior, duplicate links and competing first-link
transactions. Admin reconciliation revokes the exact old identity/session; denied
requests cannot later auto-link. Operator bootstrap is explicit, idempotent, fact-checked
and issues no session. These tests are NOT a successful real Google login.

Source tests exercise versioned corrections and immutable before/after facts, office
supersession/global DRC-HoD exclusion, source-command session revalidation after locks,
file/body/XML/formula/row limits, all-or-nothing CSV/XLSX imports, bad rows, dedupe,
concurrent commit, canonical alias corrections and forbidden merges, scoped teaching
filters, first true teaching date, continuity, rehire and leap-day pending. IO-02 and
P-54 remain pending in both source timelines and searchable policy help. No final
Silver/annual decision is inferred from those assertions.

Browser tests submit real local forms: staff/appointment creation/end/history and live
permission changes; CSV upload/preview/commit/reload and source correction; invalid row
persistence; canonical subject and teaching allocation/date correction; alias correction,
July–June year creation and duplicate rejection through canonical Admin routes; all five
distinct role dashboards with actual scoped source data; login/recovery/configuration,
read-only/deep-link denials, policy search and logout. Existing source/audit facts remain.
Browser setup ends ONLY its own leftover temporary LOCAL_E2E_TEMPORARY_OFFICE appointment
using authorized demo APIs and an audit reason, never deletion/reset.

Responsive checks: foundation 1440/1024/768/390/320 px; source forms and all five role
workspaces 1440/390/320 px. Selected axe WCAG A/AA checks report zero violations. Real
screenshots are docs/qa/phase2-completion-*.png. Desktop Admin, 320px DRC and teaching
history were visually inspected. This is not a complete manual screen-reader audit.

## Failures observed and repaired

- Outstanding startup.py Ruff formatting repaired; final 43-file formatting gate passes.
- Added full HTTP-provider test caught Authlib's convenience get() rejecting
  withhold_token. Changed JWKS fetch to request("GET", ..., withhold_token=True), which
  prevents bearer-token forwarding and passes the protocol test. Earlier fixture-state
  lookup was also corrected. Failure output retained in phase2-completion-provider-failure.txt.
- Initial Phase 2 browser run **23 passed / 4 failed**: employment route lacked expected
  appointment navigation; history assertion ran before refreshed revisions; invalid
  upload test reloaded before preview navigation; wrapped select labels included option
  text. Added the episode register/link, explicit labels and waits for actual server UI.
- Next run **26 passed / 1 failed** exposed teaching form remounting while staff sources
  loaded, clearing the entered allocation key. Form now waits for sources before mounting.
  Subsequent full 27-test run passed. Both early logs retained under phase2-completion-browser-*.
- Added canonical-reference browser test initially used the wrong alias-button label and
  uppercase error text. Corrected selectors to actual accessible labels and case-insensitive
  error assertion. Final 28-test suite passes; these were test expectation errors, not
  successful application claims. Diagnostic logs retained.
- Inventory regeneration previously overwrote later implementation policy notes. Added
  read-only --check and preserved continuation; verified retained content equality.

Non-fatal warnings: Authlib/Starlette httpx adapter deprecation and Playwright
FORCE_COLOR/NO_COLOR notice. Locked dependencies passed; no unrelated forced upgrade.

## Explicitly unverified / blocked / later phase

**Real Google integration: BLOCKED / NOT VERIFIED for all five real accounts.** No
approved Web OAuth client ID/secret, private session key, approved institutional roster
facts or voluntary participant sign-in were available. Demo database has zero linked
institutional identities. See docs/GOOGLE_OIDC_SETUP.md and fixtures/phase2-uat-roster.json
for exact prerequisites, private fields, operator commands and role acceptance script.
No runtime bypass was added to make these cases pass.

Live Google redirect/consent/Workspace policy, real HTTPS deployment, private first-Admin
roster bootstrap and five account-holder actions remain external acceptance gates.
Actual application submission/reviews/self-review transactions, quota concurrency,
provider verification, evidence/annual/Silver credit and academic separation consequences
remain Phases 3–7. Complete 80-page contracts, private attachments, cross-domain impact
previews, production DB least privilege/TLS/monitoring, backup/restore and remote CI are
not verified by this local Phase 2 suite. Unratified IO-02, Q51, P54 and role/topic
transition policies remain safely pending.

Git recovery: preserved original uncommitted source; later observed existing commit
034f71a (testing backend) during user continuation. The agent did not create a commit
or reset that checkpoint. Subsequent corrections/tests/docs remain working-tree changes.

---

## Historical verification retained below

The following sections describe earlier checkpoints, not current limitations or ports.

# Observed verification — Phase 2A, 2026-11-16

**Phase 2A source-record vertical slice verified locally. Phase 2 remains IN PROGRESS.** The Phase 1 results below are retained historical evidence; this section supersedes their current-state limitations. Native web http://127.0.0.1:5173; compiled Compose web http://127.0.0.1:8080; API docs http://127.0.0.1:8000/api/docs. Both stacks are left running with fictional data.

| Actual command / check | Observed result and evidence |
|---|---|
| `scripts/check.sh` | PASS: Ruff/format (24 files), mypy strict (17 source files), test migration upgrade, Alembic no drift, **45 PostgreSQL pytest tests**, ESLint, TypeScript, **2 Vitest tests**, Vite production build. `docs/qa/phase2a-check-final.txt` |
| Native `.venv/bin/alembic -c apps/api/alembic.ini upgrade head` | PASS; dev and separate `_test` databases upgraded from foundation through `0003_office_scope` |
| Fresh native `akus_phase2a_fresh_test` database: `alembic upgrade head`, `current`, `check`, seed twice with `AKUS_DEMO_ENABLED=true` | PASS: created new empty isolated database; output `0003_office_scope (head)`, `No new upgrade operations detected.`, two successful fictional-source seed messages. Database retained; none dropped |
| `docker compose up -d --build` | PASS: existing Phase 1 volume preserved, migration/seed exited 0, API and DB healthy. `docs/qa/phase2a-compose-build.txt`; final web rebuild logs also retained |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e` | **20 passed (27.7s)** on native. `docs/qa/phase2a-native-browser-final.txt` |
| Same browser command with `AKUS_E2E_URL=http://127.0.0.1:8080` | **20 passed (22.2s)** against compiled Vite/Caddy/FastAPI/PostgreSQL. `docs/qa/phase2a-compose-browser.txt` |
| Focused HoD source-record navigation after final scoped-link correction | **PASS: 1 native (2.0s), 1 Compose (1.4s)**. Recorded separately in `docs/qa/phase2a-native-scoped-link.txt` and `phase2a-compose-scoped-link.txt`; verifies appointment link and no end control for read-only HoD |
| `npm --prefix apps/web run lint`, `typecheck`, `format:check`; `git diff --check` | PASS after final frontend changes; generated API types include new source routes |
| `python3 scripts/scan-source.py --report docs/qa/phase2a-secret-scan.md` | PASS: 44 authored source/config files, zero limited pattern matches. Original scan report retained; scanner now refuses evidence overwrite. Not a comprehensive security audit |
| Final native and Compose proxied readiness | Both HTTP 200: `ready`, database `connected`, schema `0003_office_scope`; Compose API and DB healthy |
| Source specification hashes | Unchanged: master `f3a8fcfbef034fe76da05c6331427fa6d846b2e4c02f073934550de00e276e36`; blueprint `2c349d6ddb9fbaa61c5689aab524b830d89ec854dea61f27ddc6cc7dd9dd51c7` |

Backend checks use real PostgreSQL (no SQLite): global cross-department DRC/HoD exclusion with two competing connections; duplicate concurrent Admin source command commits once; faculty requirement; employment boundaries; exact interval adjacency; scheduled/expired offices; permission re-resolution and office end revocation without login; disabled person session invalidation; fixture role tampering cannot elevate; Principal/non-Admin mutation denial; HoD/own scope and IDOR denials; CSRF/origin and idempotency replay checks; version conflicts; immutable issued facts and audit; stable identity across two rehire episodes. Existing 21 foundation tests also remain passing. Total **45**, not 45 additional tests.

Browser flows use real form submits and persisted records: Admin creates person+initial employment/home assignment, reloads history, records an office, ends it on a dedicated source-record page, sees immutable changes; overlapping cross-department DRC/acting-HoD is rejected with inputs retained; Principal reads without writes, HoD scope filters and Faculty deep-link/API denial; two simultaneous browser contexts prove current authority changes and revocation without signing in again. Office-changing browser tests end their temporary appointments; created fictional staff/history/audit remain intentionally retained.

Accessibility: zero axe violations for selected WCAG A/AA rules on source directory/create/register/appointment-create pages at **1440, 390, 320 px**, and foundation overview at **1440, 1024, 768, 390, 320 px**. Real screenshots saved as `docs/qa/phase2a-*.png`; desktop staff history and mobile appointment form were visually inspected. This is not a full manual screen-reader/WCAG certification.

## Failures observed and fixed in this slice

- Initial TypeScript gate caught optional generated `roles`; authenticated UI handles the optional contract safely. Non-faculty Staff access also has an accurate label/eligibility message.
- Migration 0003 initially used unsupported Alembic exclusion-drop type and an unnamed expression in its create helper. Both attempts rolled back; explicit PostgreSQL exclusion DDL fixed migration application. 0003 also narrows the accidental same-role cross-department prohibition without rewriting applied 0002 history or deleting records.
- First new backend run: 15 failed / 28 passed. Test fixture references used the wrong UUID namespace keys and generated lowercase staff keys against an uppercase contract. Corrected fixtures; all 43 then passed. Added record-read and concurrent-idempotency coverage: final 45 passed. Initial failure output retained at `docs/qa/phase2a-backend-initial.txt`, later passing output at `phase2a-backend-second.txt` and final gate file.
- Initial browser run: 17 passed / 2 failed. A substring label matched the directory search before form navigation; the HoD test used a wrong search label. Corrected selectors and waited for form heading. Replaced the original modal-only ending UI with a dedicated record/end page per blueprint. Second run 19 passed, final suite with live two-session revocation 20 passed on each runtime. Initial output retained in `phase2a-browser-initial.txt`.
- Restart exposed Vite orphaned by the npm shell wrapper. `scripts/dev.sh` now owns the actual Vite process; subsequent restart released the port successfully.
- Final review changed the register's person link to the scoped office record: an office's person can have a home department outside the viewing HoD's staff scope. Focused browser checks cover the corrected link.

Warnings still observed: Starlette TestClient/httpx adapter deprecation; Playwright environment FORCE_COLOR/NO_COLOR notice. Tests pass; no forced unrelated dependency upgrade.

**Unimplemented/unverified:** real Google OIDC, verified institutional identity linking, full source corrections/rehire/teaching pages and complete role dashboards; academic applications/reviews/quotas and their concurrency; certificates, annual/Silver/separation consequences; all 80 complete page contracts; production runtime least-privilege/TLS/hardening, external provider verification, cloud deployment, remote CI, backups/restore. P-NEW-05/06 academic role-transition decisions remain POLICY_PENDING. These are not included in the passing source-only assertions.

---

## Retained Phase 1 verification — 2026-11-16 (historical snapshot)

All results below are observed locally, not planned passes. Full output: docs/qa/check-output.txt, docs/qa/browser-output.txt and docs/qa/compose-browser-output.txt. Native services are at http://127.0.0.1:5173 (web) and http://127.0.0.1:8000/api/docs (API).

| Command / verification | Observed result |
|---|---|
| `python3 scripts/spec_inventory.py` | PASS: all 2,607 lines accounted for, separate blueprint verbatim embedded, 80 unique route entries, 50 historical policies, 27 policy-register entries |
| `.venv/bin/alembic -c apps/api/alembic.ini upgrade head` | PASS on fresh local `akus` and separate `akus_test`; revision 0001_foundation |
| Test DB `alembic check` | PASS: no new upgrade operations detected |
| `scripts/check.sh` | PASS; details below |
| Ruff lint / format | PASS; 14 Python files formatted |
| mypy strict | PASS; 10 source files |
| PostgreSQL pytest | **21 passed**; includes four-contender worker transaction test, session/CSRF/expiry, origin/forged-field denial, real DB constraints and immutable audit |
| ESLint / TypeScript | PASS |
| Vitest / Testing Library | **2 passed**; pending-policy search and API error rendering |
| Vite production build | PASS; JS 361.03 kB / gzip 113.91 kB; CSS 14.40 kB / gzip 3.55 kB |
| `npm --prefix apps/web run format:check` | PASS |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" npm --prefix apps/web run e2e` | **12 passed** in final run; Chromium, real API and PostgreSQL |
| Compiled Compose browser suite | **12 passed** (9.9s) with `AKUS_E2E_URL=http://127.0.0.1:8080`; verifies compiled Vite assets, Caddy same-origin proxy, API, fresh migrated DB and local sessions |
| axe overview checks | PASS at 1440, 1024, 768, 390, 320 CSS px for selected WCAG A/AA rules; zero reported violations |
| Browser navigation | PASS: sign-in, database rows, role-appropriate demo homes, profile/help, direct reload, query persistence, denied home, logout, 404 and service failure |
| Mobile keyboard navigation | PASS: Radix navigation opens, Escape closes, trigger focus restored; scrollable year region keyboard-accessible |
| Native frontend HTTP / proxied health | 200; readiness returned `ready`, database `connected`, schema `0001_foundation` |
| `docker compose config -q` | PASS; `docker compose up -d --build` also PASS from fresh containers; migrate exited 0, API and DB healthy; Caddy frontend and readiness return HTTP 200 at port 8080 |
| `python3 scripts/scan-source.py` | PASS: 29 authored source/config files; zero matches for limited private-key/GitHub/AWS patterns. Not a comprehensive secret scan. Report retained at docs/qa/secret-scan.md |
| `git diff --check` | PASS |

Screenshots from real browser sessions: docs/qa/overview-1440.png, overview-1024.png, overview-768.png, overview-390.png, overview-320.png. Desktop and mobile images were visually inspected. Latest saved screenshots come from the compiled Compose browser run.

Initial failures and fixes: PostgreSQL could not bind a socket inside the sandbox; narrow local-process execution permission allowed the isolated server on loopback 55432. Initial browser run had 10 passes / 2 failures because mobile table overflow was not keyboard-focusable. Added a named region, tabIndex and visible focus; all 12 passed afterward. Initial lint formatting issues were fixed before the final passing check. The original accessibility finding is retained in docs/qa/initial-browser-findings.md.

Warnings: Starlette emits a deprecation notice for its httpx TestClient adapter (tests pass). npm emitted an ESLint 9 support/deprecation notice; the locked version passes checks. No forced dependency upgrade or security-audit claim was made.

Not verified / not implemented: remote CI execution; real Google OIDC; institutional effective-dated authority and complete role isolation; catalog/provider verification; topic mappings/quotas/submissions/approvals; quota races and cross-year transfers; evidence/annual/Silver/separation workflows; full 80-route coverage; production TLS/security hardening; screen-reader/manual full WCAG conformance; backup/restore. These require later phases, not fake passing tests.

Toolchain observed: Python 3.13.7, Node 24.22.1, npm 11.19.1, PostgreSQL 16.15; FastAPI 0.163.1, SQLAlchemy 2.0.57, Psycopg 3.3.9, Alembic 1.20.1, Vite 7.3.8. Exact dependency locks are checked into source. Docker 29.8.0 and Compose 5.5.1 available with narrow execution permission.

Phase 5 targeted exception suite: 7 passed against isolated PostgreSQL, including current-pool balance after concurrent rescheduling and separation. See docs/qa/phase5-separation-tests.txt.

The 0014 acceptance run in docs/qa/phase5-acceptance-checks.txt passed 221 backend tests in 71.68 seconds, 2 frontend tests, Ruff, mypy, Alembic upgrade/drift, ESLint, TypeScript, Prettier and Vite. It includes a decisive pre-separation exam, a below-Silver authentic certificate, a later exam, and a date-only ambiguous exam. Each test compared an earlier report and the current allocation. Docker image build and startup logs are phase5-build.txt and phase5-start.txt.

0015 release candidate: 234 backend tests and 2 frontend tests passed in phase5-release-checks.txt. The compiled Docker app passed 38 Playwright tests plus 2 isolated full form submissions. The preceding phase5-final-checks.txt recorded 225 passing backend tests and a Prettier failure in the new browser spec. The release run verified the formatting fix.

Recovery reproduced the completed office-rotation failure from phase5-0016-final-checks.txt. After the appointment ends, the former HoD is refused at dossier access, whereas Admin and Principal are refused academic write permission. The test now asserts both exact 403 outcomes, the unchanged pending task and seat, and a successful formally appointed acting HoD decision. The targeted test passed, followed by 236 backend tests and 2 frontend tests. A subsequent 238-test run includes both integrity/separation dispositions. Logs are phase5-office-rotation-recovery.txt, phase5-resume-checks.txt and phase5-accepted-backend.txt.

The first date-precision run passed 240 backend tests. Its full browser run passed 36 of 38. The Principal test expected named staff on the first page of a growing directory. A cross-year transfer eventually reconciled, after the 20-second browser assertion expired. Read-only inspection found 1,299 completed quota jobs and open enrollment/integrity cases. The repaired gate preserves the timeout, searches the directory through its normal UI, scopes capacity wakeups and exercises the missing-target publication race. The earlier failed log remains at docs/qa/phase5-final-acceptance-browser.txt.
