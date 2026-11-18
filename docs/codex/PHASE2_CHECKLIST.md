> Current continuation, 2026-11-18: original Phase 2 regression coverage remains in
> the passing 177-test backend suite. Expanded Phase 3 academic services are now
> implemented; older later-phase descriptions below are historical Phase 2 boundaries.
> Live Google UAT is still BLOCKED/NOT VERIFIED for all five intended participants.
> See PHASE3_CHECKLIST.md and ../../TEST_RESULTS.md for current scope and evidence.

# Phase 2 requirements and route coverage

2026-11-17. Execution authority: PHASE2_COMPLETION.md A–H, AGENTS.md and the binding master.
**Local Phase 2 implementation is verified; mandatory live Google integration remains BLOCKED.**
This matrix does not certify the whole application or all 80 complete page contracts.

All 2,607 master lines were read in bounded sections: 1–119, 120–274, 275–504,
505–731, 732–964, 965–1200, 1201–1423, 1424–1550, 1551–1777, 1778–2008,
2009–2248, 2249–2377, 2378–2484, 2485–2607. Identity/access, source-page,
Q39/Q42 and latest amendment sections were reread before their changes. No separate
onboarding/provisioning addendum exists in this checkout. The 80-page and Q01–Q50
inventories and original specification files remain intact.

## Requirement classification

“Implemented and verified” below means local PostgreSQL/API/browser evidence, not
live institutional login. Backend names refer to apps/api/tests; browser names to
apps/web/e2e. Full outputs and counts are linked from ../../TEST_RESULTS.md.

| Requirement | Classification | Implementation and verification | Remaining dependency |
|---|---|---|---|
| A Recover existing repository and Docker | Implemented and verified | Retained prior source/migrations, volume and audit; rebuilt four images, successful migrate/start; fresh DB migration gate | None locally; no reset performed |
| B Google code/PKCE/discovery/JWKS protocol | Implemented and verified locally | identity/provider.py, router.py; test_identity: real RSA signatures and isolated HTTP discovery/code/JWKS; invalid issuer/audience/time/nonce/hd/email/signature/repeated state tests | Live provider/client integration NOT VERIFIED |
| B Secure sessions/CSRF/logout/current scope | Implemented and verified | identity/service.py, access.py, people/service.py; session rotation/expiry/revocation/HTTPS-cookie/configuration tests; browser logout | HTTPS deployment itself is not tested |
| B Branded login and recovery/deep links | Implemented and verified | Login, AuthState/AuthComplete; configuration required, denied consent, expired state, account states; phase2.spec.ts | Live Google redirect/consent needs client and participant |
| C Controlled immutable subject linking | Implemented and verified | 0004/0006, official email history separate from observed email; duplicate/disabled/separated/changed-email/competing-link tests | Actual approved staff data |
| C Admin reconciliation and exact-link replacement | Implemented and verified | Accounts page + account request APIs, locked audit transaction; backend approval/denial/replacement/session revocation tests; browser scope/render checks | Populated real queue after genuine attempted login |
| C Safe first Admin bootstrap/revocation | Implemented and verified locally | identity/operator.py; operator flag, idempotency/mismatch/revocation tests; no session issued | Approved private roster and voluntary subsequent Google sign-in |
| D Five-person UAT preparation | Implemented and verified as preparation | fixtures/phase2-uat-roster.json exact addresses/intended roles, no invented source facts; GOOGLE_OIDC_SETUP.md manual script | None for template |
| D Five actual Google role sign-ins | Blocked by external credentials and account-holder action | All five explicitly BLOCKED / NOT VERIFIED; zero real identities linked in running demo DB | Approved Web client, private config, approved roster, five participants |
| E CSV/XLSX staff and teaching imports | Implemented and verified | sources/imports.py; size/shape/XML/formula limits, previews, row errors, dedupe, authorized atomic commit and race tests; real CSV browser upload/commit/reload | No role inference; offices require approved separate actions |
| E Staff/profile/employment/rehire/department/email corrections | Implemented and verified | SourceCorrection, StaffRecord/StaffSources + sources service; immutable revisions and optimistic versions; backend boundaries/rehire/revocation; browser name correction/history | Academic effects belong to Phases 4/6/7 |
| E Effective office creation/end/correction | Implemented and verified | 0002/0003/0005; current source authorization, superseded originals, DB global DRC/HoD exclusion; competing-writer tests, browser role change/end | Role-transition academic consequences POLICY_PENDING |
| E Departments/subjects/aliases/years | Implemented and verified | ReferenceSetup + source APIs; unique stable identities, alias correction with immutable history; merge rejected pending governance; July–June constraints | Quota publication Phase 3; no implicit rollover |
| E Official teaching management and first-teaching timeline | Implemented and verified | Teaching pages + API; scoped filters, effective dates, correction/void, provenance; Q39 continuity/Q42 rehire and P54 tests; browser persisted date correction | IO-02 acceptance pending; final Silver assessment Phase 6 |
| F Faculty/DRC/HoD/Admin/Principal dashboards | Implemented and verified for Phase 2 | Distinct Dashboards.tsx components and scoped source queries; five roles at 1440/390/320, axe and no fake academic state | Academic cards depend on later services |
| F Faculty→DRC→HoD, DRC own→HoD, exemptions | Partially implemented (appropriate Phase 2 boundary) | Actor eligibility/readiness route plan, separate DRC review/own navigation; HoD/Principal applicant denied; no self-review control or decision API exists | Actual route assignment, submit/review and self-review transaction tests Phase 4 |
| F Principal global read-only / Admin no automatic reviewer | Implemented and verified | Source and dashboard API guards, source-command denials, multi-department browser reads | Academic reports Phase 6/8 |
| F Quotas/applications/evidence/compliance | Not implemented — later phases | Honest authenticated NOT_IMPLEMENTED integrations, null academic counts, no decision controls | Phases 3–7; policies remain binding |
| G Docker/static/API/UI/browser gates | Implemented and verified | 109 backend + 2 UI + 28 browser; lint/type/format/build; migrations upgraded existing and fresh isolated DBs, no drift | Real Google UAT separate; remote CI not executed |
| H Persistent docs and resume instructions | Implemented | BUILD_PROGRESS, TEST_RESULTS, traceability generator, setup, manual and runbook updated | Recheck observed state each future session |

## Phase 2 page/API mapping

API prefix /api/v1. Shared scoped read APIs deliberately serve several role routes;
paths differ from some illustrative blueprint endpoints and remain generated in OpenAPI.

| Blueprint / route | Working implementation | Phase boundary |
|---|---|---|
| PUB-01 /login; PUB-02 callback; PUB-03 denied | Google begin/callback, /auth/complete, /auth/:state and /access-denied; auth/session and logout | Real Google login externally blocked |
| SHR-03 /app/profile | Own StaffRecord, employment/office/membership/email source history | Source-backed; optional self-declared skills not authoritative |
| FAC-01 /app/home; extra /drc/home | Distinct Faculty and DRC Head workspaces; GET /dashboard | Application/annual/Silver domain status unavailable |
| HOD-01 /hod/home | Scoped oversight, teaching and integration links | Review/quota mutation services later |
| PRN-01 /principal/home | Global read-only source overview | Mature reports later |
| ADM-01 /admin/home | Imports/account requests/source counts and working setup links | No academic write powers |
| ADM-02 /admin/staff; /admin/staff/new | Scoped GET /people/staff, POST /admin/staff; search/create/history | Google ownership separate |
| ADM-03 /admin/staff/:staffId | StaffRecord + StaffSources; GET /people/staff/{id}, /sources | Evidence attachment storage later; controlled identity merge pending |
| ADM-04 /admin/staff/:staffId/employment | Full source correction page, episode register; POST /admin/staff/{id}/sources | No application/Silver reconciliation preview until domain exists |
| ADM-05 /admin/appointments | Create/view/end plus source correction/supersession; /people/appointments and /admin/appointments | Active-case effects deferred, no invented resolution |
| ADM-06 /admin/teaching-assignments | TeachingList/new/detail/correct; GET /teaching, POST /admin/teaching and /{id} | Provisional source timeline, not assessed credit |
| ADM-07 /admin/academic-reference | ReferenceSetup departments/subjects/aliases; GET /sources/reference, POST /admin/reference | Canonical merges blocked, no relevance approval |
| ADM-08 /admin/academic-years | ReferenceSetup year mode with persisted July–June years | Opening/closing quotas belongs to Phase 3 |
| Supporting /admin/imports and /:importId | Stage, row preview, explicit atomic commit; /admin/imports | Real actions, no mock provider |
| Supporting /admin/accounts | Request list and audited approve/deny/exact-link reconciliation | Source-approved staff only |
| Supporting /app/system | Real readiness, worker and calendar | Foundation retained |

The 80-route inventory is a target, not 80 implemented pages. Complete mature visual
contracts, source evidence attachments and cross-domain impact previews remain partial
where their Phase 6/8 dependencies do not yet exist. No tested local behavior is
classified as a passed real-user login. No Phase 2 code item is knowingly left untested;
external integration and later-domain behavior are separately identified above.
