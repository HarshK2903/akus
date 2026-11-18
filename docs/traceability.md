# Requirements → code → API → tests

2026-11-18. Complete source inventory: spec-inventory.md. Local Phase 2 and expanded
Phase 3 slices are tested; mandatory live Google UAT remains BLOCKED. This is not
80-page or full academic workflow completion. Detailed boundaries: Phase 2 and
Phase 3 checklists in codex/. Actual commands/results/logs: ../TEST_RESULTS.md.

## Executed vertical slices

Paths below are relative to apps/api/akus unless frontend-prefixed. Backend tests are
in apps/api/tests; browser tests in apps/web/e2e. All use real PostgreSQL; OIDC protocol
fixtures are isolated test-only generated signatures/HTTP responses, not real sign-ins.

| Requirement/source | Code/schema | API/UI | Executed tests |
|---|---|---|---|
| Foundation health/calendar/worker/audit | main.py, models.py, worker.py; 0001 | health/*, foundation, academic-years; Overview | test_foundation.py; foundation.spec.ts; migration/drift checks |
| Permanent staff and episodes | people/*; 0002/0003 | people/staff, admin/staff; Staff pages | test_people.py staff/idempotency/rehire; people.spec.ts create/history |
| Effective source authority, A01–04/I01–04/I11 | access.py, people/service.py | me; all protected APIs and role homes | current/scheduled/expired office tests; scoped IDOR and write denials; browser live authority change |
| Global DRC/HoD exclusion, A02/I02 | GiST constraint; office validators | create/end/correct office pages | two competing PG writers; cross-department acting HoD conflict; immutable original facts |
| Real OIDC protocol and safe config | identity/provider.py, router.py, config.py; 0004 | begin/callback/session/logout; Login/AuthState | test_identity.py claim/signature/state/nonce/PKCE/JWKS/HTTPS-cookie tests; phase2.spec.ts configuration/recovery |
| Controlled stable identity, account queue, first Admin | identity/service.py, operator.py; 0004/0006 | admin/account-requests; Accounts; operator CLI | duplicate/racing links, changed email, blocked staff, explicit replacement/revocation, bootstrap idempotency; no real UAT |
| Source correction and history | sources/service.py; 0005 | admin/staff/{id}/sources; SourceCorrection/StaffSources | test_sources.py versions/office supersession/source history; browser name correction and reload |
| Safe CSV/XLSX import | sources/imports.py, body_limit.py | admin/imports stage/preview/commit; Imports | file limits/formula/XML, bad row rollback, retry/dedupe, concurrent commit; real CSV browser workflow |
| Teaching/reference sources, Q39/Q40/Q42 prerequisites | sources/*; 0005 | teaching, sources/reference, admin/reference; Teaching/ReferenceSetup | first-date continuity, rehire, leap day pending, correction/void, filtered scope, alias history/merge rejection; browser teaching and canonical reference/year actions |
| Five role-specific dashboards | sources/router.py; web/pages/Dashboards.tsx | dashboard, academic/integration/{area} | role routing/exemption/denials, no fake academic state; five-role responsive axe/browser |
| Current auth after transaction locks | people/service.py lock_command | all source/import/account mutations | session revocation after read, current grant recheck, command/commit races |
| Responsive usable forms and navigation | web/src/components, pages, styles.css | all source workflows plus foundation | people.spec.ts, phase2.spec.ts at 1440/390/320; foundation also 1024/768; actual screenshots |

Phase 3 code/schema/API/race evidence: [Phase 3 checklist](codex/PHASE3_CHECKLIST.md).
Source/identity writes take an exclusive authority gate; academic commands take its
shared side, then offering/application/mapping and sorted pool locks. HTTP runs outside
transactions. Source facts/audit remain immutable; no source command grants certificate credit.

## All 80 target routes

Full target roles/API contracts: route-matrix.md. Paths below are relative to
apps/web/src; API prefix /api/v1. An unavailable integration or not-found page does
not fulfill its eventual academic page contract. Extra import/account/correction
routes support the inventory and do not inflate its count.

| Page | Route | Current code / API | Implementation status | Target phase |
|---|---|---|---|---|
| PUB-01 | `/login` | `pages/Login.tsx` / auth/config, auth/google/begin, auth/demo-login | VERIFIED locally; live Google UAT BLOCKED | 2 |
| PUB-02 | `/auth/callback` | `pages/AuthState.tsx` / auth/google/callback, auth/session, me | VERIFIED protocol/recovery locally; real provider UAT BLOCKED | 2 |
| PUB-03 | `/access-denied` | `pages/AuthState.tsx, Recovery.tsx` / auth/session, me | VERIFIED pending/disabled/denied/duplicate states locally | 2 |
| PUB-04 | `/system-unavailable` | `pages/Recovery.tsx` / health/ready | VERIFIED foundation recovery | 2 |
| PUB-05 | `/not-found` | `pages/Recovery.tsx` / router | VERIFIED not-found recovery | 2 |
| SHR-01 | `/app/tasks` | None | NOT IMPLEMENTED | 8 |
| SHR-02 | `/app/notifications` | None | NOT IMPLEMENTED | 8 |
| SHR-03 | `/app/profile` | `pages/StaffRecord.tsx, components/StaffSources.tsx` / me, people/staff/{id}/sources | VERIFIED own source history; optional self-declared skills not implemented | 2 |
| SHR-04 | `/app/help` | `pages/Help.tsx` / policy/help | VERIFIED searchable policy summaries | 2 |
| SHR-05 | `/app/search` | None | NOT IMPLEMENTED | 8 |
| FAC-01 | `/app/home` | `pages/Dashboards.tsx` / dashboard; applications | VERIFIED source workspace and admission navigation; final compliance metrics later | 2 |
| FAC-02 | `/app/catalog` | `pages/academic/Catalog.tsx` / nptel/courses | VERIFIED catalog search, categories, pagination and source status | 3 |
| FAC-03 | `/app/catalog/:courseId` | `pages/academic/Catalog.tsx` / nptel/courses/{id} | VERIFIED canonical identity, exact offerings and provenance | 3 |
| FAC-04 | `/app/offerings/:offeringId` | `pages/academic/Catalog.tsx` / nptel/offerings/{id}; nptel/mapping-requests | VERIFIED exact source/dates/topic/pool/blockers, admission and mapping request | 3 |
| FAC-05 | `/app/applications` | `pages/academic/Applications.tsx` / applications | VERIFIED scoped drafts/submissions, current allocation and cases | 4 |
| FAC-06 | `/app/applications/new/offering` | `pages/academic/Applications.tsx` / nptel/offerings; applications | PARTIAL: catalog-to-draft selection; full evidence wizard later | 4 |
| FAC-07 | `/app/applications/new/eligibility` | `pages/academic/Applications.tsx` / applications; applications/{id}/submit | VERIFIED safe first-attempt declarations/reservation; evidence-dependent branches blocked | 4 |
| FAC-08 | `/app/applications/new/evidence` | `pages/academic/Applications.tsx` / applications/new wildcard | NOT COMPLETE: no evidence upload; wildcard does not satisfy evidence-page acceptance | 4 |
| FAC-09 | `/app/applications/new/review` | `pages/academic/Applications.tsx` / applications/{id}; applications/{id}/submit | PARTIAL: review/confirmation on draft detail, not a separate wizard step | 4 |
| FAC-10 | `/app/applications/:applicationId` | `pages/academic/Applications.tsx` / applications/{id}; review; withdraw; schedule-claims | VERIFIED ordinary decisions, withdrawal and personal schedule claims; broader lifecycle later | 4 |
| FAC-11 | `/app/applications/:applicationId/quota` | `pages/academic/Applications.tsx` / applications/{id} | VERIFIED original/current/official years, allocation and immutable movements | 4 |
| FAC-12 | `/app/applications/:applicationId/evidence` | None | NOT IMPLEMENTED | 4 |
| FAC-13 | `/app/applications/:applicationId/history` | `pages/academic/Applications.tsx` / applications/{id} | VERIFIED submission/source/movement/decision history; later evidence events absent | 4 |
| FAC-14 | `/app/participation/:applicationId` | None | NOT IMPLEMENTED | 6 |
| FAC-15 | `/app/previous-attempts` | None | NOT IMPLEMENTED | 6 |
| FAC-16 | `/app/previous-attempts/:attemptId` | None | NOT IMPLEMENTED | 6 |
| FAC-17 | `/app/compliance/annual` | None | NOT IMPLEMENTED | 6 |
| FAC-18 | `/app/compliance/annual/:yearId` | None | NOT IMPLEMENTED | 6 |
| FAC-19 | `/app/compliance/silver` | None | NOT IMPLEMENTED | 6 |
| FAC-20 | `/app/compliance/silver/:obligationId` | None | NOT IMPLEMENTED | 6 |
| FAC-21 | `/app/certificates` | None | NOT IMPLEMENTED | 6 |
| DRC-01 | `/drc/reviews` | `pages/academic/Applications.tsx` / applications?review=true | VERIFIED scoped review queue and no self-review; advanced queue filters later | 4 |
| DRC-02 | `/drc/reviews/:taskId` | `pages/academic/Applications.tsx` / applications/{id}/review | VERIFIED ordinary decisions, current office and DRC-own direct route; evidence exceptions later | 4 |
| DRC-03 | `/drc/history` | None | NOT IMPLEMENTED | 4 |
| HOD-01 | `/hod/home` | `pages/Dashboards.tsx` / dashboard; departments/*/quotas; applications | VERIFIED scoped sources and mapping/quota/review navigation; full metrics later | 2 |
| HOD-02 | `/hod/reviews` | `pages/academic/Applications.tsx` / applications?review=true | VERIFIED scoped review queue and no self-review; advanced queue filters later | 4 |
| HOD-03 | `/hod/reviews/:taskId` | `pages/academic/Applications.tsx` / applications/{id}/review | VERIFIED ordinary decisions, current office and DRC-own direct route; evidence exceptions later | 4 |
| HOD-04 | `/hod/topic-mappings` | `pages/academic/Governance.tsx` / departments/{id}/topic-mappings | VERIFIED department canonical-course mapping list | 3 |
| HOD-05 | `/hod/topic-mappings/requests` | `pages/academic/Governance.tsx` / departments/{id}/topic-mappings; POST nptel/mapping-requests | VERIFIED deduplicated request inbox without seat reservation | 3 |
| HOD-06 | `/hod/topic-mappings/:courseId` | `pages/academic/Governance.tsx` / departments/{id}/topic-mappings/{course} | VERIFIED source candidates, current HoD decision, effective revisions; existing-seat migration POLICY_PENDING | 3 |
| HOD-07 | `/hod/topic-mappings/:courseId/edit` | `pages/academic/Governance.tsx` / departments/{id}/topic-mappings/{course} | VERIFIED source candidates, current HoD decision, effective revisions; existing-seat migration POLICY_PENDING | 3 |
| HOD-08 | `/hod/topics` | `pages/academic/Governance.tsx` / nptel/topics; topic-proposals; admin/nptel/topics | VERIFIED canonical topics, aliases, proposals and controlled Admin maintenance | 3 |
| HOD-09 | `/hod/quotas` | `pages/academic/Governance.tsx` / departments/{id}/quotas | VERIFIED annual shared pools, filters and publication | 3 |
| HOD-10 | `/hod/quotas/:poolId` | `pages/academic/Governance.tsx` / quotas/{id}; departments/{id}/quotas | VERIFIED current HoD create/publish/revise, counted occupancy and provenance; no decrease below occupied | 3 |
| HOD-11 | `/hod/quotas/:poolId/edit` | `pages/academic/Governance.tsx` / quotas/{id}; departments/{id}/quotas | VERIFIED current HoD create/publish/revise, counted occupancy and provenance; no decrease below occupied | 3 |
| HOD-12 | `/hod/quotas/:poolId/ledger` | `pages/academic/Governance.tsx` / quotas/{id}?as_of=... | VERIFIED ledger/current reconciliation and as-of API; UI shows latest 200 movements | 3 |
| HOD-13 | `/hod/quota-transfers` | `pages/academic/Applications.tsx` / applications?reconciliation=true | VERIFIED open transfer/policy cases and retained occupancy; broader inbox filtering later | 5 |
| HOD-14 | `/hod/quota-transfers/:caseId` | `pages/academic/Applications.tsx` / quota-transfer-cases/{id}; applications/{id}/reconcile | VERIFIED scoped deep link, original/current facts, target quota link, recheck and audit | 5 |
| HOD-15 | `/hod/outcome-verifications` | None | NOT IMPLEMENTED | 6 |
| HOD-16 | `/hod/outcome-verifications/:caseId` | None | NOT IMPLEMENTED | 6 |
| HOD-17 | `/hod/integrity` | None | NOT IMPLEMENTED | 5 |
| HOD-18 | `/hod/integrity/:caseId` | None | NOT IMPLEMENTED | 5 |
| HOD-19 | `/hod/separation-cases` | None | NOT IMPLEMENTED | 7 |
| HOD-20 | `/hod/separation-cases/:caseId` | None | NOT IMPLEMENTED | 7 |
| HOD-21 | `/hod/reports/annual` | None | NOT IMPLEMENTED | 6 |
| HOD-22 | `/hod/reports/silver` | None | NOT IMPLEMENTED | 6 |
| HOD-23 | `/hod/reports/applications` | None | NOT IMPLEMENTED | 6 |
| HOD-24 | `/hod/decisions` | None | NOT IMPLEMENTED | 4 |
| PRN-01 | `/principal/home` | `pages/Dashboards.tsx: PrincipalDashboard` / dashboard | VERIFIED global read-only source oversight; academic reports later | 2 |
| PRN-02 | `/principal/departments` | None | NOT IMPLEMENTED | 8 |
| PRN-03 | `/principal/departments/:departmentId` | None | NOT IMPLEMENTED | 8 |
| PRN-04 | `/principal/applications` | None | NOT IMPLEMENTED | 8 |
| PRN-05 | `/principal/topics-quotas` | None | NOT IMPLEMENTED | 8 |
| PRN-06 | `/principal/reports/annual` | None | NOT IMPLEMENTED | 8 |
| PRN-07 | `/principal/reports/silver` | None | NOT IMPLEMENTED | 8 |
| PRN-08 | `/principal/exceptions` | None | NOT IMPLEMENTED | 8 |
| PRN-09 | `/principal/audit` | None | NOT IMPLEMENTED | 8 |
| ADM-01 | `/admin/home` | `pages/Dashboards.tsx` / dashboard; admin/nptel/provider-fetches | VERIFIED sources/imports/accounts and real public provider fetch | 2 |
| ADM-02 | `/admin/staff` | `pages/StaffDirectory.tsx, StaffNew.tsx` / people/staff, admin/staff | VERIFIED scoped search/create; Google linking separate | 2 |
| ADM-03 | `/admin/staff/:staffId` | `pages/StaffRecord.tsx, SourceCorrection.tsx` / people/staff/{id}, people/staff/{id}/sources | VERIFIED source detail/corrections; private attachments and identity merge not implemented | 2 |
| ADM-04 | `/admin/staff/:staffId/employment` | `pages/SourceCorrection.tsx` / admin/staff/{id}/sources | VERIFIED episode/rehire corrections; academic impact/evidence attachments later | 2 |
| ADM-05 | `/admin/appointments` | `pages/Appointments.tsx, AppointmentNew.tsx, AppointmentRecord.tsx, SourceCorrection.tsx` / people/appointments, admin/appointments, admin/staff/{id}/sources | VERIFIED create/end/correct/supersede and DB exclusion; active-case impacts later | 2 |
| ADM-06 | `/admin/teaching-assignments` | `pages/Teaching.tsx` / teaching, admin/teaching | VERIFIED create/filter/correct/void/timeline; IO-02 POLICY_PENDING, compliance not assessed | 2 |
| ADM-07 | `/admin/academic-reference` | `pages/ReferenceSetup.tsx` / sources/reference, admin/reference | VERIFIED canonical references/alias corrections; subject merge POLICY_PENDING | 2 |
| ADM-08 | `/admin/academic-years` | `pages/ReferenceSetup.tsx` / sources/reference; admin/reference | VERIFIED July–June years; annual quota publication on HOD pages | 2 |
| ADM-09 | `/admin/nptel-sync` | `pages/academic/Catalog.tsx` / admin/nptel/provider-fetches; nptel/courses/offerings | PARTIAL full page contract: real manual fetch/retry/accept and failure history; automated provider-job operations later | 8 |
| ADM-10 | `/admin/nptel-offerings` | `pages/academic/Catalog.tsx` / nptel/offerings/{id}; admin/nptel/offerings/{id}/accept | PARTIAL full page contract: versions/source conflicts/review verified; separate ambiguity adjudication workflow later | 8 |
| ADM-11 | `/admin/operations` | None | NOT IMPLEMENTED | 8 |
| ADM-12 | `/admin/notifications` | None | NOT IMPLEMENTED | 8 |
| ADM-13 | `/admin/audit` | None | NOT IMPLEMENTED | 8 |

## Historical and amended policy coverage

All Q01–Q50 remain reconciled in POLICY_REGISTER.md; planned domain acceptances are
in POLICY_TEST_TRACEABILITY.md. Actual application and quota races are mapped in the Phase 3 checklist.
Source tests alone do not prove quota or review correctness. Q39/Q40/Q42 source dates are tested; Silver compliance assessment is not.

A01–A08/I01–I18, J1–J16, UX-01–25, T-Q01–50, T-AMEND-01–10,
T-V2.4-TOPIC-MAP-01–05, T-ANNUAL-TOPIC-01–07, T-QUOTA-XFER-01–05 and C01–C50
remain required target coverage in master sections 15–16. Only explicitly named
tests in the checklists/results have executed; full lifecycle coverage is not claimed. Superseded HoD/Principal applicant,
dual DRC/HoD, per-offering quota and unratified mapping-credit paths stay disabled.
