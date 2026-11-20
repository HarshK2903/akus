# AKUS — PHASE 6 CONTINUATION: VERIFIED CERTIFICATES, ANNUAL COMPLIANCE & SUBJECT-WISE SILVER

## Mission
Act as a Principal Software Engineer, Staff Backend Engineer, Security Engineer, Database Transaction Architect and Senior Frontend Engineer. CONTINUE the existing AKUS repository; do not recreate it, reinitialize Git, or redo Phases 1–5. Build the Phase 6 functionality from the actual repository plan and current accepted institutional policy, not from guesses.

**Last reported checkpoint (verify independently in repository):** Phase 5 local acceptance passed with 242 PostgreSQL backend tests, 2 frontend unit tests and 38 standard Playwright journeys plus 3 isolated case submissions. Ruff, mypy, ESLint, TypeScript, formatting and production builds passed. Database migrated to `0016_archived_obligations` without observed drift; Docker application running at `http://localhost:8080` using existing persistent PostgreSQL volume, with six quota mismatch counters at zero. The report identified Phase 6 as next approved phase. Actual Google OIDC acceptance for five institutional account holders still awaits approved credentials, authoritative staff/office records and voluntary real-user login. These are reported results, not proof until you inspect current code/logs.

## 1. Recover safely and establish exact Phase 6 scope
1. Read `AGENTS.md`, `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/BUILD_PHASES.md`, current master spec, policy registry, latest UI/UX blueprint, route traceability, `docs/codex/PHASE5_CHECKLIST.md`, and existing Phase 6 checklist if one exists. Locate actual files rather than silently assuming their paths. If there is a more recent ratified policy amendment in the repository, apply it and document the precedence.
2. Inspect `git status`, branches, diffs, untracked files, migrations and current schema, Docker Compose status and recent acceptance logs. Confirm Phase 5 acceptance has not regressed. Preserve all uncommitted work, PostgreSQL volumes, audit records and credentials configuration.
3. NEVER use `docker compose down -v`, `docker volume rm`, destructive seeds, database drop/reset, hard reset, or force migration history. Ask the operator before any destructive data operation.
4. Read the repository's precise Phase 6 scope and map each requirement to existing model/service/API/UI/tests. Extend what already exists; avoid parallel/conflicting architectures.
5. Produce/update a concrete Phase 6 acceptance checklist and then immediately implement in complete vertical slices. Do not stop at planning.

## 2. Governing domain distinctions and verified achievement
- A faculty/DRC Head's **institutional NPTEL application**, **external enrollment**, **actual exam participation**, **provider certificate**, **verified institutional evidence**, **annual compliance**, **subject-wise Silver compliance**, **quota reservation** and **employment episode** are DISTINCT domain concepts with separate histories.
- The provider's course-preview metadata, a PDF upload, a manually typed mark, or a scheduled exam date do NOT independently prove an actual examination, certificate validity or user-specific enrollment. Establish evidence source, proof class, provenance, document hash, issuer identifiers, source precision, reviewer authorization and verification timestamp; make unsupported verification states explicitly pending.
- Do not call an external provider integration authoritative unless its capabilities and contracts have genuinely been verified. Integrate the existing provider registry and evidence-storage approach. External APIs may be unofficial; handle network failure, rate limits, changed schemas and stale snapshots without creating false positive fulfillment.
- Preserve immutable original evidence and append corrections/revocations/reassessments. Do not mutate historic issued reports to pretend late evidence was known earlier.

## 3. Certificate and examination evidence lifecycle
Implement the approved requirements for actual exam evidence, authentic certificates, outcomes and verification:
- Correct permanent faculty identity, employment episode, canonical NPTEL course, exact offering/run, exam sitting, actual exam date (including source and date precision), certificate reference, issue date, grade/score, percentage, verification timestamp, verified outcome and evidence provenance.
- Upload/registration, status timeline, pending review, accepted/rejected evidence with recorded rationale, malformed/duplicate/conflicting certificate handling, stable document identity/hash, and carefully scoped institutional reviewer authority. A user claiming a certificate does not automatically confer compliance.
- Protect sensitive documents; implement safe file types and limits, restricted access, audit and no secrets in logs. If source-of-truth provider verification is unavailable, keep review PENDING and avoid claiming it was verified automatically.
- Support late result verification, official grade/date corrections and revocation with append-only evidence and compliance re-evaluation. Keep state transitions concurrency-safe and idempotent.
- Maintain lifetime canonical-course certificate/no-repeat checks under Q28, including rehires, and outcome-pending restrictions under Q29–Q30. Do not conflate below-Silver valid certificates with unsuccessful/no-certificate outcomes.
- Preserve existing institutional suspension/invalidation paths under Q22–Q23 and Q33–Q34. A verified certificate must not bypass a pending integrity review or formally invalidated approval.

## 4. Annual July–June NPTEL Compliance Engine (Q35–Q38 and Q48)
Implement real, deterministically testable annual obligation assessments:
- Academic year is July 1–June 30. **Actual verified exam date** determines the year receiving completion credit (Q35), not submission, scheduled exam, course start, certificate issue or verification dates.
- Annual qualifying pathway: ONE course of at least 8 weeks with verified valid certificate, OR TWO distinct eligible 4-week courses with verified valid certificates whose actual examinations are BOTH within the SAME academic year (Q36). The annual pathway does not require 75% Silver in either case (Q37–Q38).
- Each course must independently satisfy application/institutional eligibility, external enrollment chronology, relevant exam/certificate and any score-sharing or other applicable institutional requirements; no double-credit for the same annual obligation. A single valid 4-week course alone is not enough.
- Model candidate achievement allocations, unconfirmed/pending/corrected statuses, repeat-check blocking and certificate-based recalculation. Avoid optimistic completion based on scheduled exam dates.
- Q48: Eligible genuine valid certificates issued/verified AFTER official permanent separation may retrospectively confirm the PRE-separation examination's HISTORICAL annual academic year, without reactivating employment, access, archived application or released quota. If examination was after separation, Q48 does not authorize credit.
- Immutable as-of snapshots and latest-verified reporting must be distinguishable, including when provider corrections change an earlier compliance outcome.

## 5. Subject-wise Silver Obligation Engine (Q39–Q42, Q49–Q50)
- Official effective-dated first teaching ASSIGNMENT to a canonical subject in a given employment episode starts a durable Silver obligation, with original deadline exactly two CALENDAR YEARS later (Q39). Skills/interests and self-declared expertise do not create obligations. Preserve authoritative assignment evidence, corrections, effective date and source precision.
- Continuing employment, reallocation away from the subject, transfer to another department or academic-year rollover do not reset/cancel the original subject obligation/deadline (Q40). Deduplicate against canonical subject + employment episode.
- Q41: Effective permanent separation CLOSES ACTIVE MONITORING; preserve original deadlines, historical fulfilled/outstanding/overdue-at-separation facts; never create NEW post-separation overdue violations.
- Q42: Rehiring creates a separate employment episode. New official assignment to a subject in the new episode establishes a new obligation/deadline while the prior episode's obligation remains historically closed. Certificate and canonical-course no-repeat history stay linked to permanent person identity.
- Require genuine verified certificate meeting institutional Silver threshold **>= 75%**, accepted academic subject relevance and other eligibility checks. A 65% valid certificate might qualify for annual completion, but not subject-wise Silver.
- Q50: ON-TIME Silver timeliness is based on **actual qualifying exam date ON OR BEFORE the original two-year deadline**; the later certificate issue/verification date does not make it late. Until verified, record PENDING evidence, not fulfilled. Do not backdate the verification or a decision.
- Q49: Qualifying Silver certificate issued/verified AFTER separation may retrospectively establish historical fulfillment for a relevant, eligible exam BEFORE separation and meeting the original Silver deadline. Retain the unchanged historical status-as-of-separation snapshot and append subsequent reassessment. Do not resume active monitoring, applications, reservations or access.
- Handle source-date corrections and delayed imports through auditable historical reconciliation, not by restarting clocks or deleting previous assessments. If leap-day anniversary policy is not ratified, keep a defined policy-pending path rather than guessing.
- **UNRESOLVED Q51:** Whether ONE Silver certificate can fulfill MULTIPLE distinct subject obligations is not confirmed. Never silently reuse one certificate across several subjects. Make subject-to-course mapping/claim pending in ambiguous cases, with useful UX, until ratified.

## 6. Authority, access and institutional hierarchy
- Faculty and DRC Head are the only NPTEL participant personas among the named institutional hierarchy; DRC Head is also Faculty. Ordinary Faculty review: Faculty -> DRC Head -> HoD. DRC Head's own application: directly HoD. Never allow DRC self-review.
- HoD and Principal exempt from NPTEL participation. Principal institution-wide oversight/read scope; do not grant blanket mutations or personal applicant flows. Admin controls official roster/master data but not automatic academic/certificate-final approval.
- An individual may be faculty and DRC Head, but DRC Head and HoD (including acting appointments) must never overlap; enforce appointments and reviewer authority at commit time.
- **UNRATIFIED verification authority:** prior unsuccessful/no-certificate outcomes have confirmed HoD authority, but general enrollment/certificate evidence verification authority may remain undecided. Inspect newest approved specs and do not invent an authorized reviewer. Where necessary prepare evidence, protect it with a POLICY_PENDING finalization gate, and continue implementing the approved parts. Preserve integrity-review conflict-of-interest rules.
- Imported teaching assignments are official but onboarding IO-02 HoD confirmation policy remains UNRATIFIED; do not implicitly choose which imports activate Silver obligations. Build an explicit controlled pending path if necessary and test it.

## 7. End-to-end frontend and reporting
Implement the existing phase-approved route inventory using real backend data, consistent professional spacious light-theme design, role-specific navigation, accessible controls and stateful multi-page flows:
- Faculty: exams/results/certificates uploads and history, verified/pending outcomes, annual year-by-year ledger, subject obligations, deadline and relevance evidence, request/denial states.
- DRC: same personal compliance plus allowed independent academic review.
- HoD: scoped evidence cases, documented outcome verification under approved authority, departmental annual/Silver status, unresolved/pending queues, historical changes and drilldowns.
- Principal: institution-wide read-only oversight and reproducible historical dashboards.
- Admin: authoritative staff/assignment data corrections, imports, audit and corrections; no automatic academic credential approval.
- Show source timestamps/precision, evidence provenance, verification basis and pending statuses. Distinguish scheduled exam date from actual exam date and certificate issue from verification.
- Implement filters, pagination, substantive empty/loading/error states, navigable details, accessible file upload and form validation; no placeholder actions, fake completion data or clickable dead ends.

## 8. PostgreSQL, concurrency and migration invariants
- Implement schema and Alembic migrations consistent with existing `0016_archived_obligations` head after verifying actual revision. Use PostgreSQL-backed domain transactions and append-only audit with atomic notification work ledger. Preserve source records, qualified deduplication keys and effective-dated authority.
- Ensure exactly-once fulfillment per obligation, race-safe certificate import and verification, idempotent reprocessing, no accidental double-credit to annual ledger, and reliable re-evaluation after source correction/revocation.
- Do not change quota pool identities, cross-year reservation transfer and withdrawal-vs-transfer safeguards established in prior phases. Compliance reassessment must NOT silently reopen/retarget released reservations or separation-closed applications.
- Add precise time and as-of reporting indexes; check historical before/after snapshots and migration upgrade/schema drift on both existing preserved and fresh disposable TEST databases. No reset of the existing production-like development database.
- Existing Docker Compose for web/API/worker/database remains the runtime; do not switch to native-only, wipe volumes or decide final production deployment.

## 9. Acceptance tests and regressions
Build tests before declaring a feature complete, covering at least:
- Actual vs planned examination dates across June 30/July 1 boundaries, certificate issue dates in a later year, same-year pair of two 4-week exams, cross-year pair rejection, single 4-week rejection, valid >=8-week completion with below-Silver score.
- Silver deadline based on first official teaching assignment, continuing teaching/transfer, relevance and >=75% threshold; timely exam with later issue date classified ON TIME only after verification; exam after deadline classified not on time.
- Separation-before-exam vs exam-before-separation, historical annual Q48 and historical Silver Q49, status-as-of vs latest assessment, rehire with new episode obligations and lifetime prior certificate.
- Revoked/corrected/duplicated certificate evidence, stale/forged uploads, authorization denial and independent immutable audit, integrity-review suspension, no-repeat, uncertain original teaching assignments, unknown certificate authority and unresolved multi-subject use (policy pending).
- Repeat races for same certificate, parallel verification, duplicate worker event, concurrent compliance assessment; prove one lawful outcome.
- Real frontend routes and forms through Playwright, including faculty/DRC/HoD/Principal/Admin, mobile, accessibility, protected routes, loading/errors and persistence; no misleading demo-success evidence.
- Full backend suite and targeted integration tests, frontend tests, Ruff/format/mypy, ESLint/tsc, production build, browser suite, Docker healthy services, worker heartbeat, Alembic/schema drift and live quota reconciliation.
- Run actual commands and report ACTUAL pass/fail outcomes. Do not weaken/delete tests, replace failing assertions, or mark external integrations verified using mocks.

## 10. Durable progress, external acceptance and exit gate
- Before long test/build operations and after EACH significant milestone, update `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/PHASE6_CHECKLIST.md` (or repository-equivalent), spec-to-implementation traceability, unresolved policy list and precise next command/checkpoint. Keep logs under existing `docs/qa` conventions.
- Distinguish IMPLEMENTED+TESTED, IMPLEMENTED+UNVERIFIED, POLICY_PENDING, EXTERNAL_BLOCKED and NOT_STARTED with exact evidence/paths.
- Google OIDC implementation reportedly exists, but LIVE institutional login of authorized real accounts remains unverified without approved Google OAuth configuration, staff/office assignments and voluntary account-holder sign-ins. Keep this Phase 2 external gate open and continue Phase 6 independently; never use passwords/impersonation or hardcode role grants.
- At the end, provide a concise factual summary: changed files/features, migration head, tests/results, actual browser/deployment health, known external blockers, policy questions and whether Phase 6 locally passes. Do not claim global production readiness.
- If your usage limit approaches, save handoff files IMMEDIATELY and make the next action recoverable. Do not waste the final usage budget generating prose instead of checkpointing work.

**Execute now:** Recover existing repo -> confirm Phase 5 acceptance -> implement every phase-approved Phase 6 vertical slice -> test/fix -> update durable handoff -> complete local Phase 6 acceptance. Start writing and running code; do not stop at analysis or planning.
