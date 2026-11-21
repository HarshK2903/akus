# Phase 8 local acceptance · passed 2026-11-21

Source: BUILD_PHASES.md Phase 8, PHASE8_CONTINUATION.md and the embedded page contracts in the master specification.

| Acceptance item | Verified result |
|---|---|
| Routes and roles | All 80 inventory paths resolve to explicit React pages. Browser sweeps opened all 51 fixed protected paths with the assigned roles. Public recovery paths and parameterized records are covered by workflow tests. See the [per-page matrix](../traceability.md). |
| Scoped actions and reports | The full API suite covers unauthenticated denial across 114 protected operations, current office and department scope, self-review denial, private files, personal notices, audited exports and version conflicts. |
| UI and accessibility | All 52 standard and four isolated journeys passed on the final Docker images. The private evidence form also passed its expanded 320 px axe and overflow check. [Mobile evidence](../qa/phase8-private-files-mobile.png) · [Search](../qa/phase8-verified-search-mobile.png) |
| Admission, quota and history | Full PostgreSQL coverage includes last-seat contention, withdrawal versus transfer, replays, employment changes, exact review stage and as-of compliance. All 22 operational discrepancy counters were zero after the final browser writes. |
| Build, migration and recovery | Static checks, three frontend tests, production build and all 316 backend tests passed. Migration 0021 is live on the original volume. Two separate synthetic restores matched content manifests and reconciled successfully. |
| External acceptance | Five live Google sign-ins, private provider verification, deployed malware scanning, institutional infrastructure and outstanding policy decisions remain pending. |

For a local demonstration use the [workspace and evidence walkthroughs](../USER_MANUAL.md). See [executed commands, timings and logs](../../TEST_RESULTS.md) and the [operator runbook](../OPERATIONAL_RUNBOOK.md). The approved eight-phase plan has reached its local QA gate. External owners can resume their respective acceptance tasks from the Google setup guide and policy register.

## Recovery milestones

Phase 8 recovery verified the retained Phase 7 checkpoint on main at de5844c, including its uncommitted changes. Saved results show 272 backend, two frontend, 42 standard and four isolated browser passes. All 18 discrepancy checks were zero on each of four databases. At the Phase 7 checkpoint the API and database were healthy at 0019_employment_sessions on the original volume.

| Slice | Initial finding | Acceptance |
|---|---|---|
| Role-scoped registers | 15 target pages missing across shared services, DRC, HoD, Principal and Admin | Real filtered reads, actionable links, permissions and repeatable exports |
| Notification and operations commands | Existing immutable notices and jobs lack read tracking, preferences and operations UI | Persisted per-person reads, versioned configuration and safe retry with audit |
| Navigation and page quality | Legacy pages reuse forms, no full inventory route check; initial JS 558.72 kB | Deep links, smaller initial bundle, keyboard/mobile checks, all role journeys |
| Release | Awaiting Phase 8 changes | Complete automated gates, live migration and reconciliations, deployment runbook |
| Institutional gates | External and policy pending | Preserve genuine sign-in, provider and policy boundaries |

Milestone 1: scoped register reads, personal notification privacy, version conflicts, audited exports and safe retry verified by 29 isolated backend tests. React routes and navigation implemented; browser gates pending.

Milestone 2. All 80 inventory paths resolve to explicit React routes. The PostgreSQL register/provider suite passed 33 tests, including an HTTP denial check over the protected OpenAPI inventory, exact review queues, template replay, public-source ambiguity and bounded refresh failures. Public NPTEL metadata for noc26_cs98 was retrieved by the allowlisted adapter. The source URL, observation time and content digest are in docs/qa/phase8-public-preview.txt. This observation establishes only the public course-preview contract.

2026-11-21 recovery. Both retained Compose builds and startup completed. Signed Playwright passed 51. The failed signed pytest was a repeated vacant-office alert. Corrected the delivery and comparison logic. The unchanged original assertions and restored-office repeat check pass. Private application file revisions and the remaining release checks are in verification. See [focused regression](../qa/phase8-resumed-alert.txt).

The additive application attachment migration ran on the retained database. The upgraded test DB passed 315 backend cases, including private metadata, quarantine, version conflicts, original manifests and concurrent replacements. A separate synthetic restore matched aggregate counts and evidence manifests. A second complete test gate on a fresh database includes a clean-download protocol test. Final browser and reconciliation results follow.

The release PostgreSQL gate passed all 316 backend tests after the private cache directive was preserved on downloads. A fresh schema passed all four application file regressions separately. The first full browser and isolated browser runs passed 52 and four, respectively. Both logical restores reproduced their evidence manifests, and the new consistency command asserted zero across all 22 counters on each restored copy. The final-image full browser run is in progress.
