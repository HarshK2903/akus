"""Keep full target scope separate from executable Phase 1 and 2A coverage."""
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
routes=json.loads((root/'docs/route-inventory.json').read_text())
partial={'PUB-01':('pages/Login.tsx','auth/config, auth/demo-identities, auth/demo-login','Local demo complete; Google OIDC deferred to Phase 2'), 'PUB-02':('pages/Recovery.tsx','none','Honest not-configured boundary; OIDC callback deferred'), 'PUB-03':('pages/Recovery.tsx','me','Recovery only; institutional denial details Phase 2'), 'PUB-04':('pages/Recovery.tsx','health/ready','Foundation recovery implemented'), 'PUB-05':('pages/Recovery.tsx','router','Foundation recovery implemented'), 'SHR-03':('pages/Profile.tsx','me','Local profile only; appointment history Phase 2'), 'SHR-04':('pages/Help.tsx','policy/help','Searchable source-approved summaries; full register in repository')}
for code in ['FAC-01','HOD-01','PRN-01','ADM-01']: partial[code]=('pages/Overview.tsx','foundation, academic-years','Foundation view only; academic dashboard Phase 2+')
partial.update({
    'SHR-03': ('pages/StaffRecord.tsx', 'me, me/authority, people/appointments/{id}', 'Phase 2A own identity/episode/office history; institutional OIDC/linking not yet implemented'),
    'ADM-02': ('pages/StaffDirectory.tsx, pages/StaffNew.tsx', 'GET people/staff; POST admin/staff', 'Phase 2A search, scoped reads, atomic initial source creation; roster verification/import/linking deferred'),
    'ADM-03': ('pages/StaffRecord.tsx', 'people/staff/{id}', 'Phase 2A source detail/history/appointment navigation; teaching, identity linking and correction tabs deferred'),
    'ADM-04': ('pages/StaffRecord.tsx', 'people/staff/{id}; admin/staff initial creation', 'PARTIAL: initial episode + read history including rehire; correction/separation/rehire commands not implemented'),
    'ADM-05': ('pages/Appointments.tsx, AppointmentNew.tsx, AppointmentRecord.tsx', 'people/appointments; admin/appointments; admin/appointments/{id}/end', 'Phase 2A record/view/end, scoped authority and exclusion implemented; arbitrary temporal corrections and academic impact review deferred'),
})
for code in ['FAC-01','HOD-01','PRN-01','ADM-01']:
    partial[code]=('pages/Overview.tsx', 'foundation, academic-years, current me', 'PARTIAL: source-authorized navigation and role home; full academic/source dashboards unfinished')
s='''# Requirements → code → API → tests

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

## All 80 target routes

Full roles and planned API contracts: route-matrix.md. Paths below are relative to apps/web/src; API prefix is /api/v1. Unimplemented routes recover through the real not-found page; that is not fulfillment of their contracts.

| Page | Route | Current code / API | Implementation status | Target phase |
|---|---|---|---|---|
'''
s=s.replace("## All 80 target routes", '## Implemented Phase 2A acceptance (Phase 2 still incomplete)\n\nMaster sections reread: 1095–1189, 1401–1415, 1635–1673, 1807–1830, 1901–1925, 2172–2183. Backend tests below live in `apps/api/tests/test_people.py`; browser actions in `apps/web/e2e/people.spec.ts`. Local fixtures exercise real source-schema rules; no institutional provider success is claimed.\n\n| Requirement / source | Code / schema | API / UI | Executable verification |\n|---|---|---|---|\n| Permanent identity and employment, §6 / ADM-02–04 | people/models.py; migration 0002 | POST admin/staff; StaffNew, StaffRecord | test_staff_command_atomic_idempotent_and_csrf; test_rehire_keeps_identity_and_episodes_do_not_overlap; browser create/reload/history |\n| A02/I02 global exclusive DRC/HoD, historical Q12/16 retired | GiST exclusive_drc_hod_globally; people/service.py; migrations 0002/0003 | POST admin/appointments; AppointmentNew | test_global_cross_department_exclusion_and_pending_principal; test_global_exclusion_with_two_concurrent_database_writers; browser conflict |\n| No invented same-role cross-department restriction | migration 0003 | source appointment command | test_office_boundaries_and_same_role_different_scope |\n| Current effective authority, I11 / §8 | access.py; source episodes/offices/Admin grants | me; all protected reads/commands | test_current_roles_and_filtered_reads; test_scheduled_and_expired_offices_grant_nothing; test_demo_role_label_cannot_elevate_and_disabled_staff_session_revoked |\n| A01/A02/I01 eligibility boundary (academic intake still absent) | Actor.view | me / Profile | parametrized eligible Faculty+DRC; exempt HoD/acting/Principal; no application API |\n| A04/I04 Principal read-only global source visibility | access.py, staff_scope / require_admin | people/staff, people/appointments; read-only pages | test_non_admin_cannot_write_even_with_csrf; browser Principal denial; academic oversight pending |\n| Scoped and own-record privacy | service.detail, appointment_detail | staff and office detail / profile | test_current_roles_and_filtered_reads; test_appointment_record_reads_require_own_or_scoped_authority; HoD and Faculty browser denials |\n| Authority ending without login refresh; Q17 prerequisite only | end_appointment; server-time versioned source end | AppointmentRecord full page; profile | test_appointment_changes_live_session_authority_and_end_revokes; two-browser source-change/revocation workflow |\n| Original facts and immutable changes | office trigger, audit events, command receipts | staff/office history | test_end_is_versioned_idempotent_and_preserves_issued_record; direct SQL UPDATE/DELETE rejected |\n| CSRF/origin/idempotency/optimistic concurrency | mutation_guard; lock_command; commit_command | all source commands | test_staff_command_atomic_idempotent_and_csrf; test_duplicate_concurrent_source_command_commits_once; test_authority_rechecked_before_idempotent_replay |\n| Pending authority never implies a new approver | authority + create_appointment | AUTHORITY_POLICY_PENDING; readable error | test_global_cross_department_exclusion_and_pending_principal; POLICY_GAPS.md |\n| Responsive usable source pages | web/pages/Staff*, Appointment* | real forms, source history, full end page, read-only variants | people.spec.ts; axe at 1440/390/320, actual screenshots; native and compiled Compose |\n\nExtra functional routes supporting these contracts: `/admin/staff/new`, `/admin/appointments/new`, `/admin/appointments/:appointmentId`, `/people/staff`, `/people/staff/:staffId`, `/people/appointments`, `/people/appointments/:appointmentId`. They do not inflate the canonical 80-page inventory. Department/episode correction, OIDC/linking, teaching and complete dashboards are unfinished Phase 2 work.\n\n' + "## All 80 target routes")
for r in routes:
    code=r['id']; phase=2
    if code.startswith('FAC'):
        n=int(code[-2:]);phase=3 if 2<=n<=4 else 4 if 5<=n<=13 else 6 if n>=14 else 2
    if code.startswith('DRC'): phase=4
    if code.startswith('HOD'):
        n=int(code[-2:]);phase=2 if n==1 else 4 if n in [2,3,24] else 3 if 4<=n<=12 else 5 if n in [13,14,17,18] else 7 if n in [19,20] else 6
    if code.startswith('PRN'):phase=2 if code=='PRN-01' else 8
    if code.startswith('ADM'):phase=2 if int(code[-2:])<=8 else 8
    if code.startswith('SHR'):phase=2 if code in ['SHR-03','SHR-04'] else 8
    if code in partial:
        f,a,status=partial[code];current=f'`{f}` / {a}'
    else:current='None';status='NOT IMPLEMENTED'
    s+=f"| {code} | `{r['route']}` | {current} | {status} | {phase} |\n"
s+='''
## Historical policy coverage

All fifty reconciled rows are in POLICY_REGISTER.md with source lines and planned T-Q01–T-Q50 acceptance. Detailed owning modules, target UI and planned test references are in POLICY_TEST_TRACEABILITY.md. No Phase 1 demo-role test substitutes for institutional office/approval policy coverage. Negative applicant, topic-quota, cross-year and compliance tests must run with their actual domain services in later phases.

## Additional complete source inventories (planned tests)

A01–A08 and I01–I18: master 1403–1410 and 1656–1673. J1–J16 journeys: 1254–1284. UX-01–UX-25: 1357–1381. T-Q01–T-Q50, T-AMEND-01–10, T-V2.4-TOPIC-MAP-01–05, T-ANNUAL-TOPIC-01–07, T-QUOTA-XFER-01–05: section 15, lines 2190–2266. C01–C50 adversarial scenarios: 2270–2319. All remain planned except the foundation and source-authority assertions explicitly listed above. No academic review, active-case transition or compliance calculation is implemented by those assertions. No quota concurrency proof is claimed from the local work-ledger concurrency test.
'''
(root/'docs/traceability.md').write_text(s)
s='# Policy-to-module / UI / test plan\n\nThese are PLANNED academic domain tests. Limited executed source prerequisites are explicitly marked PARTIAL; they do not complete a historical policy test. Retired rules require negative runtime tests. Reconciled wording is in POLICY_REGISTER.md; no superseded branch may be revived.\n\n| Policy | Owner planned | Target pages | Planned acceptance | Status |\n|---|---|---|---|---|\n'
for i in range(1,51):
    owner,ui=('quota/applications','HOD-09–12; FAC-06–13') if i<=9 else ('identity/reviews','ADM-05; DRC-01–03; HOD-02–03') if i<=18 else ('applications/integrity/outcomes','FAC-06–16; HOD-15–18') if i<=34 else ('annual compliance','FAC-17–18; HOD-21; PRN-06') if i<=38 else ('Silver/employment','FAC-19–20; ADM-04/06; HOD-22') if i<=42 else ('separation/history','HOD-19–20; ADM-04; FAC-13/17–20')
    status = 'PARTIAL: source office exclusion tested in test_people.py; no academic routing engine' if i in [12,16] else 'PARTIAL: current source authority/revocation tested; academic queue reassignment absent' if i == 17 else 'PARTIAL: permanent identity and episode history tested; Silver/certificate consequences absent' if i == 42 else 'NOT IMPLEMENTED'
    s+=f'| Q-{i:02} | {owner} | {ui} | T-Q{i:02} | {status} |\n'
(root/'docs/POLICY_TEST_TRACEABILITY.md').write_text(s)
print('Traceability refreshed: 80 routes, 50 policy rows, explicit Phase 1/2A coverage and unfinished scope.')
