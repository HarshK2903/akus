# Phase 4 applications and reviews

Local build-plan acceptance passed on 2026-11-19. The implementation continues the Phase 3 admission and transfer work on 4743023. The binding master and embedded blueprint remain unchanged.

| Requirement | Verified implementation and evidence |
|---|---|
| Draft, resume and submit | Faculty and DRC routes preserve draft revisions, academic relevance and declarations. An eligible submission takes a single seat atomically and snapshots its source, mapping, route and prior findings. test_admission.py, test_participation.py and phase3/phase4 Playwright journeys. |
| Current departmental authority | Faculty goes to DRC then HoD. DRC's own application goes directly to a distinct HoD. Exempt roles, promotion conflicts and overlapping offices retain the established server and PostgreSQL guards. test_admission.py, test_people.py and browser role journeys. |
| Enrollment order and late decisions | Person/run-specific asserts and current HoD findings preserve exact or date-only precision. Indeterminate order stays pending. The current HoD may authenticate a documented current extension at final review. Expiry leaves the held seat in place. Q19–22 in test_participation.py. |
| Voluntary withdrawal and rejection | A pre-start enrolled applicant requests a separate HoD decision. Rejection or authorized release acts on the current pool. Post-start voluntary withdrawal retains occupancy. Concurrent transfer, duplicate receipts, terminal history and independent Q24/Q25 reapplication are tested. |
| Canonical attempts and no-repeat | Permanent person + exact run identifies the attempt. Its canonical course drives repeat eligibility. Assertions, evidence revisions and independent HoD findings are immutable. Valid certificate prohibits repeat. Verified no-certificate permits a new admission subject to all other gates. test_outcomes.py and phase4.spec.ts. |
| Corrections and audit | Finding revisions retain actual observation, source digest, office and rationale. Corrected earlier certificate after newer approval opens a formal recognition hold and preserves the counted seat. Correction versus final approval is tested with concurrent PostgreSQL transactions. Final disposition remains authority-pending. |
| Runtime verification | 0012 at head, no drift, 210 backend, 2 frontend and 36 Playwright tests passed. Integrity query reported 0 inconsistent pools and 0 invalid transfer pairs. See TEST_RESULTS.md and docs/qa/phase4-final-* logs. |

## Local demonstration

1. Open http://127.0.0.1:8080 and choose a fictional Faculty identity. In Course catalog open an exact offering with an accepted current source, approved primary topic and published capacity. Save a draft with relevance and declarations, resume it, review and submit. Application detail shows the held seat and pending DRC office.
2. Sign in as the matching demo DRC, open its review queue and approve. Sign in as the department HoD and record the final decision. For a DRC applicant the submission goes straight to HoD.
3. On an active Faculty application record a documentary enrollment assertion. As its HoD inspect actual source precision, record a finding, and compare the enrollment with the immutable submission time. Before commencement the applicant can request withdrawal. The HoD can authorize the release, and the ledger shows the current pool and release reason.
4. From a prior exact offering use **Report a prior attempt**. Submit its official archive reference, checksum, observed time and rationale. As HoD open **Prior-result verification**, find the offering and record the independent finding. As Faculty reopen **My prior attempts** to see repeat eligibility and history. A verified no-certificate finding itself reserves zero seats.
5. The reproducible synthetic browser journey creates a fresh canonical course, two exact runs, mapping and capacity. It records a no-certificate finding, submits a fresh application, then corrects the prior result. The DRC cannot approve the repeat. See apps/web/e2e/phase4.spec.ts and docs/qa/phase4-final-browser.txt.

## Boundaries at handoff

The user-confirmed Q19/Q20 verifier is the current department HoD or acting HoD. General evidence verification and final integrity disposition require separate authority. Phase 5 covers exceptional case operations and deadlines. Phase 6 covers private uploads, provider certificate lifecycle, actual exams and annual/Silver credit. Google OAuth client configuration, approved staff and office records, and voluntary participation of the five designated account holders are external requirements. Local demo tests provide no real account-holder sign-in result.
