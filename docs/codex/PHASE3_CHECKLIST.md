# Phase 3 requirements and recovery checkpoint

2026-11-18. Existing main/034f71a plus all uncommitted source/migrations preserved.
Governing PHASE3_CONTINUATION.md was read completely; master/blueprint inventory and
hashes are unchanged. This continuation expands Phase 3 to admission and rescheduling
boundaries from planned Phases 4/5. It does not complete later evidence/compliance work.

Current local core/expanded admission-transfer gate: PASS (177 backend, 2 UI, 33
browser tests; migrations/build/quality/health verified). See ../../TEST_RESULTS.md
for executed commands, later copy-only checks and explicit remaining boundaries.
Do not infer live Google acceptance or production readiness from local demo proof.

## Implemented requirements and evidence

Paths are relative to apps/api/akus unless stated. PostgreSQL tests are in
apps/api/tests; browser workflows in apps/web/e2e/phase3.spec.ts. All application
commands require authenticated current authority, CSRF, source/reason and idempotency.

| Requirement | Implementation / migration | Actual verification and boundary |
|---|---|---|
| Canonical course vs exact offering | catalog/models, provider, service, router; 0007 | test_catalog: exact identity, normalization, category/dates/duration, public HTTPS only, unavailable/schema mismatch. Catalog/course/offering and Admin source pages; live public fetch succeeded |
| Immutable metadata provenance and conflicts | ProviderSnapshot/Fetch + append-only events; 0007 | Digest/URL/trust/parser/observed time, source acceptance/version; newer conflict blocks old-source admission and stale acceptance. Original submission is not rewritten |
| Topic registry/aliases/proposals | catalog models/service; 0007 | Canonical normalization/alias uniqueness, proposals and current-role writes; topic list/detail and controlled source forms |
| One primary charging topic per department/canonical course | mapping anchor, effective revision with exclusion; 0007 | HoD/current acting HoD only, source candidates and academic rationale; faculty cannot pick charging topic; racing revisions and mapping-vs-submit tested |
| Missing mapping/cap cannot submit | mapping requests, admission guards | Draft + deduplicated request permitted, no allocation; browser Faculty request → HoD mapping → publication |
| Annual shared quota | quotas; 0007/0009 | Unique department/topic/July–June key; separate annual publication, no automatic cap; permanent key and no unpublish. Courses share capacity; cap decrease vs submit/transfer tested |
| Atomic admission and immutable snapshot | applications/service, models; 0008 | Source/deadline/declaration/no-repeat/exemption guards; one HELD allocation, policy/mapping/source snapshot, ledger/audit/notice/receipt. Last shared seat and same canonical two-offering races |
| Review hierarchy and scope | applications/service, router | Faculty→DRC→HoD and DRC-own→HoD, no self-review, current office rechecked, Principal read-only, Admin lacks academic authority. Approved seat CONFIRMED; rejection releases current pool |
| Withdrawal vs transfer exactly once | offering/app locks, current allocation pool lock, deferred ledger/count guards | Original concurrency test retained; deterministic withdrawal-first repro failed 423 pre-fix, passes after commencement-specific fix. Conflicting start date still blocks; audit captures accepted commencement source/digest |
| Cross-year provider reschedule | applications/transfers; 0008/0009 | Sorted source+target pool locks; same topic only; balanced transfer pair + pointer + notice/audit atomically. Missing/unpublished/full retains source. Repeat/older/same-year/roundtrip/last-target-seat/closure races |
| Personal official scheduled date | applications/personal_schedule; 0010 | User-confirmed current HoD authority; unverified Faculty claim cannot transfer. Exact applicant/offering, no self-verification, immutable source/digest/observation/office/rationale. Two people in same run can have different charge years; no actual-exam/compliance inference |
| Reconciliation and durable work | cases, notices, worker QUOTA_RECHECK | Quota publication/release queues rechecks; target capacity revalidated. In-app notices, no email claim. Closed release resolves work without verifying claim or deciding policy; original evidence retained |
| Real UI and navigation | web/src/pages/academic, lib/academic, main.tsx | Catalog, source fetch/versions, topic/mapping, quota edit/publish/ledger, applications/reviews/withdrawal, schedule claim/verification, case inbox/deep link/recheck. Accessible landmarks, 1440/390/320 screenshots, original source pages retained |
| History, scope and as-of | submissions/ledger/events/notices; quota_history | Original/current/official scheduled year separate; own Faculty ledger privacy and global Principal reads. API as-of aggregation; UI latest 200 movements. Source command current-session and scoped case-ID denials |
| Docker and safe migration continuity | existing Compose, migrations 0001–0010 | Existing volume retained; fresh isolated DB chain/head/drift and seed twice; live readiness must match 0010. OpenAPI and generated TS refreshed |

## Explicit non-completions and policy boundaries

- **External blocked / NOT VERIFIED:** Phase 2 real Google client/private session key,
  approved five-person staff/office records and voluntary account-holder sign-ins.
  GOOGLE_OIDC_SETUP.md lists exact configuration. No passwords or impersonation.
  Source imports/identity/authorization regression tests pass independently.
- **POLICY_PENDING:** P-NEW-11 existing-seat cross-topic remapping; P-NEW-10 permanent
  failed-transfer remedy/priority; applicant exemption transitions; emerging-tech
  exception authority; IO-02 teaching acceptance; P-54 leap-day; Q51 multi-subject credit.
  Preserve counted allocations/audit, create pending cases, grant no automatic waiver.
- **Not implemented (Phases 4–7):** private evidence upload/storage, verified external
  enrollment/late-enrollment exceptions, Q04 enrolled-before-start release verification,
  prior no-certificate result workflow, genuine certificate/actual-exam verification,
  final annual/Silver credit, integrity/separation/rehire academic consequences.
  These are future implementation, not missing Google credentials or invented policy.
- **Partial full page contracts (Phase 8):** complete multi-step evidence wizard,
  advanced inbox filtering/pagination of older ledger events, automated provider sync
  job operations and separate ambiguity adjudication. Current source fetch is real and
  synchronous/manual; worker handles quota reconciliation only. No dead retry button.
- **Not production-ready:** local demo credentials/database owner, no tested production
  TLS/least-privilege/PITR/evidence retention deployment. No cloud action performed.

## Recovery actions and next phase

Original /tmp final-check log was absent after restart. Original race test passed five
repetitions; deterministic withdrawal-first reproduction exposed the source-status
precondition race, preserved in docs/qa/phase3-withdrawal-ordered-failure.txt. It was
not a reproduced double-decrement: locking/current-pool release was retained, while
withdrawal now evaluates the source field it actually depends on. Newer conflicting
commencement stays blocked; exam-only conflicts still block new admission.

Final logs now live in docs/qa, not only /tmp. Preserve previous failures and results.
Do not rewrite earlier phases. Next complete the remaining Phase 4 evidence-dependent
application slice, then Phase 5 exception lifecycle and Phase 6 compliance. Real Google
UAT can proceed independently only when the authorized external prerequisites exist.
