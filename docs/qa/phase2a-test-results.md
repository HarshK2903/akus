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
