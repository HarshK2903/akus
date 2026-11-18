# Phase 3 active continuation — recovered 2026-11-17

**IN PROGRESS; not a Phase 3 completion claim.** Previous Phase 2 report below is retained as history. The newer `docs/codex/PHASE3_CONTINUATION.md` authorizes Phase 3 while live Google UAT remains externally blocked. Existing main/034f71a and all uncommitted work, original PostgreSQL volume and data preserved.

Recovered after host interruption: Docker services had exited 255; same Compose services restarted. Current code passes Ruff and mypy (47 modules). The old foundation test asserted that submission routes did not exist; replaced that obsolete Phase 1 condition with real route-contract checks plus mandatory 401 for all unauthenticated application commands. Authentication checks are intact. Race test sessions now use independent authenticated browser sessions instead of rotating away the competing token.

Implemented catalog/provider normalization, canonical topics/aliases/proposals, HoD effective mapping revisions, annual pools/publication, application drafts and atomic HELD reservations, immutable submission snapshots, DRC→HoD/direct-HoD reviews, permitted withdrawal, dual-pool cross-year transfer/retain+flag, durable in-app notifications and worker reconciliation. New React pages expose those records and commands. No provider enrollment, certificate or annual-compliance claim is inferred.

Latest completed gate before additional hardening: **159 PostgreSQL tests passed** (`/tmp/akus-phase3-races-checks2.log`). Earlier full gate: 150 backend + 2 frontend tests, lint/format/typechecks/build passed. Catalog browser workflow passed in the previous continuation; newly repeated full browser gate had 29 passed / 2 failed (one stale Phase 2 placeholder expectation and one missing source-confirmation checkbox in the new test). Those are repaired and rerunning. Additive migrations 0007/0008 applied; 0009 adds permanent quota-key/balanced-transfer guards and is currently being verified. Do not infer current final results from previous counts.

Next: finish current gates, repair any failure, fresh database migration/drift proof, real public provider smoke, full browser verification, traceability/setup updates. Expanded Phase 3 acceptance still needs individual hall-ticket schedule evidence handling and remaining evidence-dependent branches. Do not label them external blockers or complete until implemented/tested. Phase 4–7 compliance, evidence and exceptional lifecycle work remains distinct. All five live Google UAT cases remain unverified without private OAuth configuration, approved source roster facts and voluntary account-holder login.


This is the recovered historical checkpoint, superseded by current root documents.
