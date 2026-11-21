"""Generate all 80 routes and 50 policies with explicit tested vs future boundaries."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
routes = json.loads((root / 'docs/route-inventory.json').read_text())
implemented = {
    'PUB-01': ('pages/Login.tsx', 'auth/config, auth/google/begin, auth/demo-login', 'VERIFIED locally; live Google UAT BLOCKED'),
    'PUB-02': ('pages/AuthState.tsx', 'auth/google/callback, auth/session, me', 'VERIFIED protocol/recovery locally; real provider UAT BLOCKED'),
    'PUB-03': ('pages/AuthState.tsx, Recovery.tsx', 'auth/session, me', 'VERIFIED pending/disabled/denied/duplicate states locally'),
    'PUB-04': ('pages/Recovery.tsx', 'health/ready', 'VERIFIED foundation recovery'),
    'PUB-05': ('pages/Recovery.tsx', 'router', 'VERIFIED not-found recovery'),
    'SHR-03': ('pages/StaffRecord.tsx, components/StaffSources.tsx', 'me, people/staff/{id}/sources', 'VERIFIED own source history; optional self-declared skills not implemented'),
    'SHR-04': ('pages/Help.tsx', 'policy/help', 'VERIFIED searchable policy summaries'),
    'FAC-01': ('pages/Dashboards.tsx: FacultyDashboard / DrcDashboard', 'dashboard, academic/integration/{area}', 'VERIFIED source workspace; academic metrics/services later'),
    'HOD-01': ('pages/Dashboards.tsx: HodDashboard', 'dashboard', 'VERIFIED scoped source oversight; review/quota services later'),
    'PRN-01': ('pages/Dashboards.tsx: PrincipalDashboard', 'dashboard', 'VERIFIED global read-only source oversight; academic reports later'),
    'ADM-01': ('pages/Dashboards.tsx: AdminDashboard', 'dashboard', 'VERIFIED import/account/source tasks; provider integrations unavailable'),
    'ADM-02': ('pages/StaffDirectory.tsx, StaffNew.tsx', 'people/staff, admin/staff', 'VERIFIED scoped search/create; Google linking separate'),
    'ADM-03': ('pages/StaffRecord.tsx, SourceCorrection.tsx', 'people/staff/{id}, people/staff/{id}/sources', 'VERIFIED source detail/corrections; private attachments and identity merge not implemented'),
    'ADM-04': ('pages/SourceCorrection.tsx', 'admin/staff/{id}/sources', 'VERIFIED episode/rehire corrections; academic impact/evidence attachments later'),
    'ADM-05': ('pages/Appointments.tsx, AppointmentNew.tsx, AppointmentRecord.tsx, SourceCorrection.tsx', 'people/appointments, admin/appointments, admin/staff/{id}/sources', 'VERIFIED create/end/correct/supersede and DB exclusion; active-case impacts later'),
    'ADM-06': ('pages/Teaching.tsx', 'teaching, admin/teaching', 'VERIFIED create/filter/correct/void/timeline; IO-02 POLICY_PENDING, compliance not assessed'),
    'ADM-07': ('pages/ReferenceSetup.tsx', 'sources/reference, admin/reference', 'VERIFIED canonical references/alias corrections; subject merge POLICY_PENDING'),
    'ADM-08': ('pages/ReferenceSetup.tsx', 'sources/reference, admin/reference', 'VERIFIED July–June year creation; publication/quotas later'),
}
implemented.update(json.loads((root / 'docs/phase3-route-coverage.json').read_text()))
implemented.update(json.loads((root / 'docs/phase4-route-coverage.json').read_text()))
implemented.update(json.loads((root / 'docs/phase5-route-coverage.json').read_text()))
implemented.update(json.loads((root / 'docs/phase6-route-coverage.json').read_text()))
implemented['ADM-04'] = ('pages/SourceCorrection.tsx, components/EmploymentChanges.tsx', 'admin/staff/{id}/sources, admin/staff/{id}/rehire, admin/employment-episodes/{id}/impact and permanent-separation', 'Employment corrections, read-only impact preview, atomic rehire and order recording. Browser coverage in phase5.spec.ts and phase7.spec.ts.')

implemented.update(json.loads((root / 'docs/phase8-route-coverage.json').read_text()))

s = '''# Requirements → code → API → tests

The [full-system acceptance matrix](qa/FINAL_REQUIREMENTS_MATRIX.md) reconciles the current source, permissions, all 80 pages and the historical policies with executed audit evidence. [Release gates](qa/RELEASE_READINESS_GATE.md).

Phase 8 passed its local release gate on 2026-11-21 at 0021_application_files with 316 backend, three frontend, 52 standard browser and four isolated browser passes. All 80 inventory paths resolve. The register, authorization, provider, browser, application attachment and operational checks are indexed in the [Phase 8 acceptance checklist](codex/PHASE8_CHECKLIST.md).

Phase 7 local acceptance passed at migration 0019 with 272 backend tests, two frontend tests, 42 standard browser journeys and four additional isolated journeys. [Phase 7 acceptance](codex/PHASE7_CHECKLIST.md).

2026-11-20. Phase 6 local acceptance passed with 266 backend tests, two frontend tests, 40 standard and four additional isolated browser journeys. [Acceptance checklist](codex/PHASE6_CHECKLIST.md) · [Test results](../TEST_RESULTS.md) · [Database reconciliation](qa/phase6-signed-ledgers.txt). Previous phase checklists retain their executed results. The inventory covers 80 target routes and 50 historical policies. Live institutional Google sign-in remains externally blocked.

## Executed vertical slices

Paths below are relative to apps/api/akus unless frontend-prefixed. Backend tests are
in apps/api/tests; browser tests in apps/web/e2e and apps/web/qa. All use real PostgreSQL; OIDC protocol
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

The personal episode history route `/app/history` supports the blueprint's Q41–Q49 journey with `me/employment-episodes/{eid}/history`. It links each earlier episode to its annual/Silver reports and closures. [Phase 7 checklist](codex/PHASE7_CHECKLIST.md).

Phase 6 sources are compliance/* and migrations 0017–0018. Certificate, annual, Silver and as-of reporting evidence is indexed in [the Phase 6 checklist](codex/PHASE6_CHECKLIST.md), test_compliance.py, e2e/phase6.spec.ts and qa/credential.spec.ts.

Phase 5 quota event coverage includes a first pool publication racing a missing destination, scoped worker wakeups and exactly-once release across concurrent exception cases. The immutable ledger is reconciled with current allocations using scripts/verify-quota.sql.

Phase 5 employment, integrity, retrospective credit and office-alert evidence: [Phase 5 checklist](codex/PHASE5_CHECKLIST.md).

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
'''
for route in routes:
    code = route['id']
    n = int(code[-2:])
    phase = 2
    if code.startswith('FAC'):
        phase = 3 if 2 <= n <= 4 else 4 if 5 <= n <= 13 else 6 if n >= 14 else 2
    elif code.startswith('DRC'):
        phase = 4
    elif code.startswith('HOD'):
        phase = 2 if n == 1 else 4 if n in [2, 3, 24] else 3 if 4 <= n <= 12 else 5 if n in [13, 14, 17, 18] else 5 if n in [19, 20] else 6
    elif code.startswith('PRN'):
        phase = 2 if n == 1 else 8
    elif code.startswith('ADM'):
        phase = 2 if n <= 8 else 8
    elif code.startswith('SHR'):
        phase = 2 if n in [3, 4] else 8
    if code in implemented:
        file, api, status = implemented[code]
        current = f'`{file}` / {api}'
    else:
        current, status = 'None', 'NOT IMPLEMENTED'
    s += f"| {code} | `{route['route']}` | {current} | {status} | {phase} |\n"
s += '''
## Historical and amended policy coverage

All Q01–Q50 remain reconciled in POLICY_REGISTER.md; planned domain acceptances are
in POLICY_TEST_TRACEABILITY.md. Actual application and quota races are mapped in the Phase 3 checklist.
Phase 7 reuses the earlier separation and assessment services and adds episode-bound sessions, atomic administrative rehire, impact preview, personal history and historical register membership. [Phase 7 coverage](codex/PHASE7_CHECKLIST.md).

Phase 5 introduced frozen separation status. Phase 6 joins the active and archived credential histories and tests current and retrospective annual and subject results.

A01–A08/I01–I18, J1–J16, UX-01–25, T-Q01–50, T-AMEND-01–10,
T-V2.4-TOPIC-MAP-01–05, T-ANNUAL-TOPIC-01–07, T-QUOTA-XFER-01–05 and C01–C50
remain required target coverage in master sections 15–16. Only explicitly named
tests in the checklists/results have executed; full lifecycle coverage is not claimed. Superseded HoD/Principal applicant,
dual DRC/HoD, per-offering quota and unratified mapping-credit paths stay disabled.
'''
(root / 'docs/traceability.md').write_text(s)
s = '''# Policy-to-module / UI / test plan

These distinguish tested academic slices from planned lifecycle work. Source
prerequisites alone do not complete historical policy acceptance. Reconciled active/superseded
wording is in POLICY_REGISTER.md. Negative tests must prevent retired runtime paths.

| Policy | Owner planned | Target pages | Planned acceptance | Status |
|---|---|---|---|---|
'''
policy_status = json.loads((root / 'docs/phase3-policy-coverage.json').read_text())
policy_status.update(json.loads((root / 'docs/phase4-policy-coverage.json').read_text()))
policy_status.update(json.loads((root / 'docs/phase5-policy-coverage.json').read_text()))
policy_status.update(json.loads((root / 'docs/phase6-policy-coverage.json').read_text()))
policy_status["41"] += " Phase 7 freezes the teaching revision known at the effective boundary (test_delayed_hr_order_freezes_teaching_revision_known_at_effective_instant)."
policy_status["42"] += " Atomic rehire preserves identity, scoped history and session revocation (test_mixed_departure_rehire_and_private_episode_history and test_institutional_session_requires_fresh_sign_in_after_rehire)."
policy_status["45"] += " Phase 7 mixes Q45 and Q47 in one episode and races a permanent order with final HoD approval."
policy_status["48"] += " Historical roster membership and search labels survive later source corrections (test_historical_register_survives_backdated_staff_corrections)."
for retired in ("31", "32"):
    policy_status[retired] = "Retired by A01/A07. Applicant exemptions and current independent HoD prior-result authority are exercised by test_admission.py and test_outcomes.py."
for i in range(1, 51):
    owner, ui = ('quota/applications', 'HOD-09–12; FAC-06–13') if i <= 9 else ('identity/reviews', 'ADM-05; DRC-01–03; HOD-02–03') if i <= 18 else ('applications/integrity/outcomes', 'FAC-06–16; HOD-15–18') if i <= 34 else ('annual compliance', 'FAC-17–18; HOD-21; PRN-06') if i <= 38 else ('Silver/employment', 'FAC-19–20; ADM-04/06; HOD-22') if i <= 42 else ('separation/history', 'HOD-19–20; ADM-04; FAC-13/17–20')
    status = 'PARTIAL: source office exclusion and eligible route metadata tested' if i in [12, 16] else 'PARTIAL: source authority/revocation tested; academic reassignment absent' if i == 17 else 'PARTIAL: first official date, continuity and provisional anniversary tested; final Silver credit absent' if i in [39, 40] else 'PARTIAL: permanent identity and new-episode first-teaching clock tested; academic consequences absent' if i == 42 else 'NOT IMPLEMENTED'
    status = policy_status.get(str(i), status)
    s += f'| Q-{i:02} | {owner} | {ui} | T-Q{i:02} | {status} |\n'
(root / 'docs/POLICY_TEST_TRACEABILITY.md').write_text(s)
assert len(routes) == 80
print('Traceability refreshed: 80 routes, 50 policy rows; Phase 2–8 implementation and external acceptance boundaries.')
