# AKUS implementation plan

Binding sources: spec/AKUS_MASTER_SPEC.txt (complete inventory, latest V2.4),
codex/BUILD_PHASES.md, expanded codex/PHASE3_CONTINUATION.md and the confirmed
policy/HALL_TICKET_AUTHORITY_2026-11-18.md. Read BUILD_PROGRESS, TEST_RESULTS,
traceability and POLICY_GAPS before resuming. Preserve existing working-tree changes.

## Architecture and transactions

React 19/TypeScript/Vite/Router/TanStack Query calls same-origin /api/v1 through Caddy.
FastAPI/Python 3.13 uses synchronous SQLAlchemy/Psycopg 3 and PostgreSQL 16. Existing
Compose services/volume remain authoritative; Alembic migrations are forward-only.

Identity owns Google protocol, stable subject links, account reconciliation and opaque
sessions. People resolves permanent staff, employment, department and current effective
offices. Sources owns validated imports, corrections, reference data and teaching.
Catalog owns canonical courses vs exact offerings, immutable bounded public-provider
observations, topics/aliases/proposals and effective HoD primary-topic decisions.
Quotas owns published department/topic/July–June pools and revisions. Applications
coordinates immutable submission facts, single counted allocation, balanced ledger,
review/withdrawal, person-specific schedule verification, transfers and reconciliation.
The worker processes durable quota rechecks; notices are persisted in-app, not emailed.

Academic commands take a shared source-authority advisory gate; identity/source changes
use the exclusive side. Per-person command keys serialize retries. Resource order is
offering → application → mapping anchor → sorted source/target pools. Authority and
versions are revalidated after locks. Provider HTTP happens outside DB transactions.
One commit includes allocation, pool count, immutable ledger/event/notice and receipt.
Deferred PostgreSQL constraints check allocation/ledger/count agreement and balanced
transfer pairs. Exclusion constraints prevent effective DRC/HoD overlap globally.
Current-role checks at the API are authoritative; frontend controls only aid navigation.

## Work order and acceptance gates

| Phase | Current delivered scope | Remaining gate/work |
|---|---|---|
| 0 | Entire 2,607-line master, 80 target routes, historical Q01–50 reconciled | Preserve source hashes/inventory and pending-policy register |
| 1 | Docker/PostgreSQL/API health/worker/React foundation | Included in every regression run |
| 2 | Identity/linking/bootstrap, people/imports/corrections/teaching, five dashboards | Real Google private configuration, approved source roster and five voluntary account-holder UATs |
| 3 expanded | Catalog, topic governance, annual publication/occupancy; admission/reviews and official/person-specific atomic transfers required by continuation | See Phase 3 checklist and TEST_RESULTS for actual gate status; no implicit credit/compliance |
| 4 | Safe first-attempt draft/admission, normal review, withdrawal/rejection already delivered | Finish evidence-dependent chronology/prior-result/late-enrollment branches and complete wizard, without reimplementing existing admission |
| 5 | Provider/personal schedule transfer, retained failed transfer, reconciliation already delivered | Broader integrity/authority rotation/deadline exceptions; policy-pending branches remain blocked |
| 6 | No final compliance implementation | Secure evidence intake, authorized independent verification, actual-exam annual and separate Silver assessment; IO-02/Q51/P54 gates |
| 7 | Current allocation history/as-of query available | Separation/rehire academic consequences, retrospective credit and exception workflows |
| 8 | Working responsive source/academic pages and automation | Remaining route contracts, advanced reports/operations, production hardening and tested backup restore |

Each vertical slice is schema → transaction/service/API authorization → usable pages
→ PostgreSQL unit/integration/concurrency tests → browser workflow/accessibility and
responsive evidence → durable docs. Gates: scripts/check-docker.sh, existing Docker
build/up, additive migration/current/drift checks, Playwright on :8080. Use separate
retained *_test databases; never reset/truncate audit or delete Docker volumes.

## Recovery checkpoint

Migrations 0001–0006 are preserved. Additions: 0007 catalog/mapping/annual pools,
0008 admission/allocation/transfer ledger, 0009 permanent quota identity/balanced pair,
0010 immutable person-specific schedule findings and evidence-bound movements.
Current head: 0010_personal_schedule. Generated OpenAPI/TypeScript contract is refreshed.

Source-only exam-date conflict does not invalidate an unchanged verified commencement
for lawful withdrawal. Any newer conflicting commencement, stale/unavailable source or
unverified enrollment exception still blocks. Offering/app locks serialize transfer and
release, and withdrawal records the accepted commencement source/digest/date.

Next implement the remaining Phase 4 evidence-dependent vertical slice, then Phase 5
exceptional lifecycle and Phase 6 assessment. Real Google UAT proceeds independently
when authorized configuration/account holders are available; never use demo results as
real institutional acceptance. POLICY_PENDING is preserved for unratified decisions.
