# Requirements → code → API → tests

Status as of 2026-11-16. Master specification is binding; complete source coverage is in spec-inventory.md. This matrix distinguishes actual executable foundation/source workflows from planned academic behavior. No full business policy or all-80-page completion is claimed.

## Implemented Phase 1 acceptance

| Requirement | Code/schema | API/UI | Actual tests |
|---|---|---|---|
| PostgreSQL foundation / forward migration | apps/api/akus/models.py; migrations/versions/0001_foundation_phase_1_foundation.py | health/ready, academic-years | test_live_ready_openapi, test_seed_idempotent_and_year_constraints; Alembic check |
| Honest DB health / safe errors | apps/api/akus/main.py | health/live, health/ready, Overview, Recovery | test_unavailable_database_not_green; browser backend failure |
| Local identity opt-in / production blocked | apps/api/akus/config.py, seed.py | Login, auth/config | test_demo_disabled_and_production_fail_closed |
| Server-resolved fixture identity | apps/api/akus/auth.py | auth/demo-login, me, Profile | test_demo_identity_is_server_resolved (six fixtures), test_forged_fields_origin_and_identity_denied |
| Protected reads | apps/api/akus/main.py current dependency | me, academic-years, foundation, policy/help | test_reads_require_session (four endpoints) |
| Session/CSRF expiry/revocation | models.AuthSession, auth.py | auth/demo-login, auth/logout | test_logout_csrf_and_revocation; test_login_rotates_session_and_expiry_is_enforced |
| Immutable foundation audit | models.AuditEvent, DB triggers | local login/logout/worker | test_audit_database_immutability (UPDATE, DELETE) |
| Transactional local worker claim | work_jobs, worker_heartbeats, worker.py | foundation status | test_worker_claim_once_under_concurrency (four real PG sessions) |
| Explicit policy pending | akus/policy.py, POLICY_GAPS.md | policy/help, Help | test_pending_rules_not_confirmed; Help.test.tsx |
| Light responsive shell and accessible navigation | web/src/styles.css, components/Shell.tsx | home/profile/help and recovery | foundation.spec.ts: widths 1440/1024/768/390/320, axe, dialog focus restore |
| Real browser navigation and recoverable failure | pages/*, lib/api.ts | /login, role homes, profile/help | foundation.spec.ts: login, reload, denied deep link, policy URL, logout, failure and 404 |
| Contract and quality | docs/openapi.json, web/src/lib/schema.d.ts, scripts/check.sh | /api/openapi.json, /api/docs | Ruff, mypy, ESLint, TypeScript, Vitest, Vite build |

Backend tests: `apps/api/tests/test_foundation.py`; UI tests: `apps/web/src/pages/Help.test.tsx`; browser tests: `apps/web/e2e/foundation.spec.ts`. Test results and limits: ../TEST_RESULTS.md.

## Implemented Phase 2A acceptance (Phase 2 still incomplete)

Master sections reread: 1095–1189, 1401–1415, 1635–1673, 1807–1830, 1901–1925, 2172–2183. Backend tests below live in `apps/api/tests/test_people.py`; browser actions in `apps/web/e2e/people.spec.ts`. Local fixtures exercise real source-schema rules; no institutional provider success is claimed.

| Requirement / source | Code / schema | API / UI | Executable verification |
|---|---|---|---|
| Permanent identity and employment, §6 / ADM-02–04 | people/models.py; migration 0002 | POST admin/staff; StaffNew, StaffRecord | test_staff_command_atomic_idempotent_and_csrf; test_rehire_keeps_identity_and_episodes_do_not_overlap; browser create/reload/history |
| A02/I02 global exclusive DRC/HoD, historical Q12/16 retired | GiST exclusive_drc_hod_globally; people/service.py; migrations 0002/0003 | POST admin/appointments; AppointmentNew | test_global_cross_department_exclusion_and_pending_principal; test_global_exclusion_with_two_concurrent_database_writers; browser conflict |
| No invented same-role cross-department restriction | migration 0003 | source appointment command | test_office_boundaries_and_same_role_different_scope |
| Current effective authority, I11 / §8 | access.py; source episodes/offices/Admin grants | me; all protected reads/commands | test_current_roles_and_filtered_reads; test_scheduled_and_expired_offices_grant_nothing; test_demo_role_label_cannot_elevate_and_disabled_staff_session_revoked |
| A01/A02/I01 eligibility boundary (academic intake still absent) | Actor.view | me / Profile | parametrized eligible Faculty+DRC; exempt HoD/acting/Principal; no application API |
| A04/I04 Principal read-only global source visibility | access.py, staff_scope / require_admin | people/staff, people/appointments; read-only pages | test_non_admin_cannot_write_even_with_csrf; browser Principal denial; academic oversight pending |
| Scoped and own-record privacy | service.detail, appointment_detail | staff and office detail / profile | test_current_roles_and_filtered_reads; test_appointment_record_reads_require_own_or_scoped_authority; HoD and Faculty browser denials |
| Authority ending without login refresh; Q17 prerequisite only | end_appointment; server-time versioned source end | AppointmentRecord full page; profile | test_appointment_changes_live_session_authority_and_end_revokes; two-browser source-change/revocation workflow |
| Original facts and immutable changes | office trigger, audit events, command receipts | staff/office history | test_end_is_versioned_idempotent_and_preserves_issued_record; direct SQL UPDATE/DELETE rejected |
| CSRF/origin/idempotency/optimistic concurrency | mutation_guard; lock_command; commit_command | all source commands | test_staff_command_atomic_idempotent_and_csrf; test_duplicate_concurrent_source_command_commits_once; test_authority_rechecked_before_idempotent_replay |
| Pending authority never implies a new approver | authority + create_appointment | AUTHORITY_POLICY_PENDING; readable error | test_global_cross_department_exclusion_and_pending_principal; POLICY_GAPS.md |
| Responsive usable source pages | web/pages/Staff*, Appointment* | real forms, source history, full end page, read-only variants | people.spec.ts; axe at 1440/390/320, actual screenshots; native and compiled Compose |

Extra functional routes supporting these contracts: `/admin/staff/new`, `/admin/appointments/new`, `/admin/appointments/:appointmentId`, `/people/staff`, `/people/staff/:staffId`, `/people/appointments`, `/people/appointments/:appointmentId`. They do not inflate the canonical 80-page inventory. Department/episode correction, OIDC/linking, teaching and complete dashboards are unfinished Phase 2 work.

## All 80 target routes

Full roles and planned API contracts: route-matrix.md. Paths below are relative to apps/web/src; API prefix is /api/v1. Unimplemented routes recover through the real not-found page; that is not fulfillment of their contracts.

| Page | Route | Current code / API | Implementation status | Target phase |
|---|---|---|---|---|
| PUB-01 | `/login` | `pages/Login.tsx` / auth/config, auth/demo-identities, auth/demo-login | Local demo complete; Google OIDC deferred to Phase 2 | 2 |
| PUB-02 | `/auth/callback` | `pages/Recovery.tsx` / none | Honest not-configured boundary; OIDC callback deferred | 2 |
| PUB-03 | `/access-denied` | `pages/Recovery.tsx` / me | Recovery only; institutional denial details Phase 2 | 2 |
| PUB-04 | `/system-unavailable` | `pages/Recovery.tsx` / health/ready | Foundation recovery implemented | 2 |
| PUB-05 | `/not-found` | `pages/Recovery.tsx` / router | Foundation recovery implemented | 2 |
| SHR-01 | `/app/tasks` | None | NOT IMPLEMENTED | 8 |
| SHR-02 | `/app/notifications` | None | NOT IMPLEMENTED | 8 |
| SHR-03 | `/app/profile` | `pages/StaffRecord.tsx` / me, me/authority, people/appointments/{id} | Phase 2A own identity/episode/office history; institutional OIDC/linking not yet implemented | 2 |
| SHR-04 | `/app/help` | `pages/Help.tsx` / policy/help | Searchable source-approved summaries; full register in repository | 2 |
| SHR-05 | `/app/search` | None | NOT IMPLEMENTED | 8 |
| FAC-01 | `/app/home` | `pages/Overview.tsx` / foundation, academic-years, current me | PARTIAL: source-authorized navigation and role home; full academic/source dashboards unfinished | 2 |
| FAC-02 | `/app/catalog` | None | NOT IMPLEMENTED | 3 |
| FAC-03 | `/app/catalog/:courseId` | None | NOT IMPLEMENTED | 3 |
| FAC-04 | `/app/offerings/:offeringId` | None | NOT IMPLEMENTED | 3 |
| FAC-05 | `/app/applications` | None | NOT IMPLEMENTED | 4 |
| FAC-06 | `/app/applications/new/offering` | None | NOT IMPLEMENTED | 4 |
| FAC-07 | `/app/applications/new/eligibility` | None | NOT IMPLEMENTED | 4 |
| FAC-08 | `/app/applications/new/evidence` | None | NOT IMPLEMENTED | 4 |
| FAC-09 | `/app/applications/new/review` | None | NOT IMPLEMENTED | 4 |
| FAC-10 | `/app/applications/:applicationId` | None | NOT IMPLEMENTED | 4 |
| FAC-11 | `/app/applications/:applicationId/quota` | None | NOT IMPLEMENTED | 4 |
| FAC-12 | `/app/applications/:applicationId/evidence` | None | NOT IMPLEMENTED | 4 |
| FAC-13 | `/app/applications/:applicationId/history` | None | NOT IMPLEMENTED | 4 |
| FAC-14 | `/app/participation/:applicationId` | None | NOT IMPLEMENTED | 6 |
| FAC-15 | `/app/previous-attempts` | None | NOT IMPLEMENTED | 6 |
| FAC-16 | `/app/previous-attempts/:attemptId` | None | NOT IMPLEMENTED | 6 |
| FAC-17 | `/app/compliance/annual` | None | NOT IMPLEMENTED | 6 |
| FAC-18 | `/app/compliance/annual/:yearId` | None | NOT IMPLEMENTED | 6 |
| FAC-19 | `/app/compliance/silver` | None | NOT IMPLEMENTED | 6 |
| FAC-20 | `/app/compliance/silver/:obligationId` | None | NOT IMPLEMENTED | 6 |
| FAC-21 | `/app/certificates` | None | NOT IMPLEMENTED | 6 |
| DRC-01 | `/drc/reviews` | None | NOT IMPLEMENTED | 4 |
| DRC-02 | `/drc/reviews/:taskId` | None | NOT IMPLEMENTED | 4 |
| DRC-03 | `/drc/history` | None | NOT IMPLEMENTED | 4 |
| HOD-01 | `/hod/home` | `pages/Overview.tsx` / foundation, academic-years, current me | PARTIAL: source-authorized navigation and role home; full academic/source dashboards unfinished | 2 |
| HOD-02 | `/hod/reviews` | None | NOT IMPLEMENTED | 4 |
| HOD-03 | `/hod/reviews/:taskId` | None | NOT IMPLEMENTED | 4 |
| HOD-04 | `/hod/topic-mappings` | None | NOT IMPLEMENTED | 3 |
| HOD-05 | `/hod/topic-mappings/requests` | None | NOT IMPLEMENTED | 3 |
| HOD-06 | `/hod/topic-mappings/:courseId` | None | NOT IMPLEMENTED | 3 |
| HOD-07 | `/hod/topic-mappings/:courseId/edit` | None | NOT IMPLEMENTED | 3 |
| HOD-08 | `/hod/topics` | None | NOT IMPLEMENTED | 3 |
| HOD-09 | `/hod/quotas` | None | NOT IMPLEMENTED | 3 |
| HOD-10 | `/hod/quotas/:poolId` | None | NOT IMPLEMENTED | 3 |
| HOD-11 | `/hod/quotas/:poolId/edit` | None | NOT IMPLEMENTED | 3 |
| HOD-12 | `/hod/quotas/:poolId/ledger` | None | NOT IMPLEMENTED | 3 |
| HOD-13 | `/hod/quota-transfers` | None | NOT IMPLEMENTED | 5 |
| HOD-14 | `/hod/quota-transfers/:caseId` | None | NOT IMPLEMENTED | 5 |
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
| PRN-01 | `/principal/home` | `pages/Overview.tsx` / foundation, academic-years, current me | PARTIAL: source-authorized navigation and role home; full academic/source dashboards unfinished | 2 |
| PRN-02 | `/principal/departments` | None | NOT IMPLEMENTED | 8 |
| PRN-03 | `/principal/departments/:departmentId` | None | NOT IMPLEMENTED | 8 |
| PRN-04 | `/principal/applications` | None | NOT IMPLEMENTED | 8 |
| PRN-05 | `/principal/topics-quotas` | None | NOT IMPLEMENTED | 8 |
| PRN-06 | `/principal/reports/annual` | None | NOT IMPLEMENTED | 8 |
| PRN-07 | `/principal/reports/silver` | None | NOT IMPLEMENTED | 8 |
| PRN-08 | `/principal/exceptions` | None | NOT IMPLEMENTED | 8 |
| PRN-09 | `/principal/audit` | None | NOT IMPLEMENTED | 8 |
| ADM-01 | `/admin/home` | `pages/Overview.tsx` / foundation, academic-years, current me | PARTIAL: source-authorized navigation and role home; full academic/source dashboards unfinished | 2 |
| ADM-02 | `/admin/staff` | `pages/StaffDirectory.tsx, pages/StaffNew.tsx` / GET people/staff; POST admin/staff | Phase 2A search, scoped reads, atomic initial source creation; roster verification/import/linking deferred | 2 |
| ADM-03 | `/admin/staff/:staffId` | `pages/StaffRecord.tsx` / people/staff/{id} | Phase 2A source detail/history/appointment navigation; teaching, identity linking and correction tabs deferred | 2 |
| ADM-04 | `/admin/staff/:staffId/employment` | `pages/StaffRecord.tsx` / people/staff/{id}; admin/staff initial creation | PARTIAL: initial episode + read history including rehire; correction/separation/rehire commands not implemented | 2 |
| ADM-05 | `/admin/appointments` | `pages/Appointments.tsx, AppointmentNew.tsx, AppointmentRecord.tsx` / people/appointments; admin/appointments; admin/appointments/{id}/end | Phase 2A record/view/end, scoped authority and exclusion implemented; arbitrary temporal corrections and academic impact review deferred | 2 |
| ADM-06 | `/admin/teaching-assignments` | None | NOT IMPLEMENTED | 2 |
| ADM-07 | `/admin/academic-reference` | None | NOT IMPLEMENTED | 2 |
| ADM-08 | `/admin/academic-years` | None | NOT IMPLEMENTED | 2 |
| ADM-09 | `/admin/nptel-sync` | None | NOT IMPLEMENTED | 8 |
| ADM-10 | `/admin/nptel-offerings` | None | NOT IMPLEMENTED | 8 |
| ADM-11 | `/admin/operations` | None | NOT IMPLEMENTED | 8 |
| ADM-12 | `/admin/notifications` | None | NOT IMPLEMENTED | 8 |
| ADM-13 | `/admin/audit` | None | NOT IMPLEMENTED | 8 |

## Historical policy coverage

All fifty reconciled rows are in POLICY_REGISTER.md with source lines and planned T-Q01–T-Q50 acceptance. Detailed owning modules, target UI and planned test references are in POLICY_TEST_TRACEABILITY.md. No Phase 1 demo-role test substitutes for institutional office/approval policy coverage. Negative applicant, topic-quota, cross-year and compliance tests must run with their actual domain services in later phases.

## Additional complete source inventories (planned tests)

A01–A08 and I01–I18: master 1403–1410 and 1656–1673. J1–J16 journeys: 1254–1284. UX-01–UX-25: 1357–1381. T-Q01–T-Q50, T-AMEND-01–10, T-V2.4-TOPIC-MAP-01–05, T-ANNUAL-TOPIC-01–07, T-QUOTA-XFER-01–05: section 15, lines 2190–2266. C01–C50 adversarial scenarios: 2270–2319. All remain planned except the foundation and source-authority assertions explicitly listed above. No academic review, active-case transition or compliance calculation is implemented by those assertions. No quota concurrency proof is claimed from the local work-ledger concurrency test.
