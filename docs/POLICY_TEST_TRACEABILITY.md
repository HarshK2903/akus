# Policy-to-module / UI / test plan

These distinguish tested academic slices from planned lifecycle work. Source
prerequisites alone do not complete historical policy acceptance. Reconciled active/superseded
wording is in POLICY_REGISTER.md. Negative tests must prevent retired runtime paths.

| Policy | Owner planned | Target pages | Planned acceptance | Status |
|---|---|---|---|---|
| Q-01 | quota/applications | HOD-09–12; FAC-06–13 | T-Q01 | VERIFIED amended annual topic rule: catalog/admission tests cover shared pool, cap, publication, mapping and reservation races; historical per-offering rule disabled |
| Q-02 | quota/applications | HOD-09–12; FAC-06–13 | T-Q02 | VERIFIED amended annual topic rule: catalog/admission tests cover shared pool, cap, publication, mapping and reservation races; historical per-offering rule disabled |
| Q-03 | quota/applications | HOD-09–12; FAC-06–13 | T-Q03 | VERIFIED lawful pre-enrollment/pre-start release, post-start retention, rejection and current-pool release; withdrawal/transfer ordering tested |
| Q-04 | quota/applications | HOD-09–12; FAC-06–13 | T-Q04 | Q04 request, current HoD finding/authorization, release from current charged pool, identical-key replay and transfer race in test_participation.py. |
| Q-05 | quota/applications | HOD-09–12; FAC-06–13 | T-Q05 | VERIFIED lawful pre-enrollment/pre-start release, post-start retention, rejection and current-pool release; withdrawal/transfer ordering tested |
| Q-06 | quota/applications | HOD-09–12; FAC-06–13 | T-Q06 | VERIFIED lawful pre-enrollment/pre-start release, post-start retention, rejection and current-pool release; withdrawal/transfer ordering tested |
| Q-07 | quota/applications | HOD-09–12; FAC-06–13 | T-Q07 | VERIFIED amended annual topic rule: catalog/admission tests cover shared pool, cap, publication, mapping and reservation races; historical per-offering rule disabled |
| Q-08 | quota/applications | HOD-09–12; FAC-06–13 | T-Q08 | VERIFIED amended annual topic rule: catalog/admission tests cover shared pool, cap, publication, mapping and reservation races; historical per-offering rule disabled |
| Q-09 | quota/applications | HOD-09–12; FAC-06–13 | T-Q09 | A published annual topic cap cannot drop below current occupancy. Changes wake only seats waiting for capacity in this department/topic/year. test_admission.py covers quota reduction and first publication racing the verified reschedule. |
| Q-10 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q10 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-11 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q11 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-12 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q12 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-13 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q13 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-14 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q14 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-15 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q15 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-16 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q16 | VERIFIED ordinary amended Faculty→DRC→HoD / DRC-own→HoD; no HoD/Principal applicant; emerging exception authority POLICY_PENDING |
| Q-17 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q17 | Current office follows pending task. Previous decisions keep their original reviewer and office. Current coverage and both external cutoffs are visible in review-office-alerts. test_hod_rotation_during_pending_review_preserves_drc_decision_and_seat verifies the vacancy, all three denials and the newly appointed acting HoD. |
| Q-18 | identity/reviews | ADM-05; DRC-01–03; HOD-02–03 | T-Q18 | Vacancy preserves the held seat. Durable scoped office notices and published dates are covered in test_exception_cases.py. Admin and Principal cannot substitute. |
| Q-19 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q19 | Flag elapsed cutoff and hold seat. Final HoD must verify submission-first enrollment or document a current official extension. test_participation.py. |
| Q-20 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q20 | Verified enrollment after valid submission permits ordinary approval, including when the published deadline passed. test_participation.py. |
| Q-21 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q21 | Pre-submission enrollment blocks submission and held seat. Same-day date-only evidence cannot establish order. test_participation.py. |
| Q-22 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q22 | Later verified early enrollment opens a case and suspends recognition. Current allocation and approval history remain visible. Phase 5 browser dossier. |
| Q-23 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q23 | Case-specific formally designated independent reviewer may invalidate. One ledger release from current pool. A pending separation task links the invalidation without manufacturing a chronology finding. Repeated processing cannot release twice. Prior participant/approver may not decide. No role-wide mandate. |
| Q-24 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q24 | Fresh independent admission after rejection reruns canonical, enrollment, date, source and capacity gates. test_participation.py. |
| Q-25 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q25 | Fresh admission after withdrawal requires no enrollment and pre-commencement. test_participation.py. |
| Q-26 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q26 | A person can hold distinct canonical courses concurrently. test_participation.py. |
| Q-27 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q27 | Canonical active uniqueness across exact runs. Real PostgreSQL race in test_admission.py. |
| Q-28 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q28 | Verified valid certificate permanently bars same-person canonical repeats regardless of score. test_outcomes.py. |
| Q-29 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q29 | Unresolved prior outcomes block admission. Verified no-certificate finding permits fresh consideration. test_outcomes.py. |
| Q-30 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q30 | Current distinct department HoD verifies exact-person/run evidence and can leave it unresolved. Immutable history. test_outcomes.py and phase4.spec.ts. |
| Q-31 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q31 | NOT IMPLEMENTED |
| Q-32 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q32 | NOT IMPLEMENTED |
| Q-33 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q33 | Prior certificate correction opens the newer case. Distinct adjudication, preserved evidence/approval history and original certificate. |
| Q-34 | applications/integrity/outcomes | FAC-06–16; HOD-15–18 | T-Q34 | Upheld case resolves only that application; it keeps its seat and is eligible for independent assessment. General active compliance/evidence engine is Phase 6. |
| Q-35 | annual compliance | FAC-17–18; HOD-21; PRN-06 | T-Q35 | Historical Q48 assessment selects official July–June year of actual exam, independent of scheduled pool and issuance. Active compliance engine is Phase 6. |
| Q-36 | annual compliance | FAC-17–18; HOD-21; PRN-06 | T-Q36 | Historical annual report allows one qualifying course of at least eight weeks or two distinct four-week canonical courses in the actual exam year. |
| Q-37 | annual compliance | FAC-17–18; HOD-21; PRN-06 | T-Q37 | Historical report groups four-week evidence by actual academic year and distinct canonical course. Duplicate or cross-year pairing cannot satisfy the obligation. |
| Q-38 | annual compliance | FAC-17–18; HOD-21; PRN-06 | T-Q38 | Genuine qualifying historical annual certification can count below Silver. Score threshold enforced separately for each subject. |
| Q-39 | Silver/employment | FAC-19–20; ADM-04/06; HOD-22 | T-Q39 | PARTIAL: first official date, continuity and provisional anniversary tested; final Silver credit absent |
| Q-40 | Silver/employment | FAC-19–20; ADM-04/06; HOD-22 | T-Q40 | PARTIAL: first official date, continuity and provisional anniversary tested; final Silver credit absent |
| Q-41 | Silver/employment | FAC-19–20; ADM-04/06; HOD-22 | T-Q41 | Permanent HR order freezes episode-level first assignment, deadline and status. Late verification adds a separate assessment without post-departure overdue marks. |
| Q-42 | Silver/employment | FAC-19–20; ADM-04/06; HOD-22 | T-Q42 | Rehire starts new episode/teaching clock. Former frozen assessment and lifetime certified canonical no-repeat remain attached to the correct records. |
| Q-43 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q43 | Pre-enrollment and pre-commencement release via confirmed chronology or separately appointed independent negative-roster check. Mere absence stays pending. |
| Q-44 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q44 | Verified enrollment before pre-start departure holds until current department HoD/acting HoD documents closure. A late date-only enrollment source is sufficient when the days establish the order; ambiguous same-day evidence stays held. See PostgreSQL branch/replay/denial tests. |
| Q-45 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q45 | Permanent post-start separation releases current pool, including after migration. Distinct from retained voluntary withdrawal. |
| Q-46 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q46 | Uses departure effective time and verified commencement, preserving recorded source and actual later adjudication time. |
| Q-47 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q47 | Date-only same-day case remains counted for current HoD. Precise order or documented indeterminacy closes with immutable decision and one release. |
| Q-48 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q48 | Case-specific authentic pre-separation exam/certificate and participation evidence can reassess historical annual completion. No reactivation. Earlier as-of query preserved. |
| Q-49 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q49 | One relevant verified Silver result may confirm a frozen episode-specific obligation with an independent, documented pre-existing institutional ruling. A teaching row alone leaves IO-02 pending. Separate later relevance assessment supported; second subject is policy pending. |
| Q-50 | separation/history | HOD-19–20; ADM-04; FAC-13/17–20 | T-Q50 | Verified actual exam date determines deadline inclusion, separately from issuance and review time. Exact boundary, late, below threshold, and unknown chronology are tested. |
