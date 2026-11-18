# NPTEL source and Phase 3 workflow guide

Use the existing Docker application at http://127.0.0.1:8080. This installation is
explicitly LOCAL/DEMO. Fictional test identities are not real institutional UAT.
Google private setup remains in GOOGLE_OIDC_SETUP.md; public course metadata requires
no Google sign-in or provider account, but AKUS source mutations require current Admin.

## Real public metadata

1. Admin → NPTEL provider sources (`/admin/nptel-sync`). Record a canonical course
   only after identifying it; an exact offering/run is a separate record. Search/select
   the canonical source course and enter an exact ID such as `noc26_cs98`.
2. Record the official source reference and reason, confirm identity, then Fetch.
   The adapter contacts only the fixed public NPTEL HTTPS host, with bounded response
   size/time, no redirects, exact context-path verification and explicit schema checks.
   A failure persists a provider check and reason; retry the fetch after investigation.
3. On offering detail inspect dates, duration, categories, trust, observation time,
   digest and source. Accept only the applicable exact observation with a reason.
   A newer conflicting observation requires review; an older source cannot clear it.
4. `/admin/nptel-offerings` searches recorded courses/runs and opens their metadata
   versions and fetch history. Submission snapshots never change with this maintenance.

The observed public endpoint is
https://onlinecourses.nptel.ac.in/e-learning/api/coursepreview?course_id=noc26_cs98.
Its payload is a JSON-encoded string; the adapter normalizes academic fields only,
converts timestamps to IST and strips markup. It ignores anonymous enrollment flags
and unrelated contact fields. The smoke course `PUBLIC_NPTEL_NOC26_CS98` already exists:
do not duplicate it. Its real dates are historical; no open eligibility is implied.
It is deliberately AWAITING_SOURCE_ACCEPTANCE. Observed digest/status: qa/phase3-live-provider.txt.

`AKUS_NPTEL_SNAPSHOT_MAX_AGE_SECONDS` defaults to 3600 (permitted 60–86400). This is an
engineering freshness gate, not a new institutional deadline. It is wired through
Compose for API/worker/migrate. Stale/unavailable source blocks new admission. A changed
scheduled-exam field does not invalidate an unchanged accepted commencement for
withdrawal; a conflicting commencement still requires verified source resolution.
There is no background provider cron or genuine NPTEL enrollment/certificate adapter.

## Demonstrating the complete local workflow

Use the conspicuously synthetic fixtures created by the Phase 3 Playwright suite. It
creates fresh local observations through an API available only in explicit demo mode
to an authenticated demo Admin. These observations are labeled LOCAL_DEMO, never
OFFICIAL_HTTPS. Run the existing E2E command in README; data/audit remain persistent.

1. Faculty (Mira) opens catalog and an exact offering. Request missing HoD mapping;
   a draft/request reserves nothing. Faculty cannot select the quota topic.
2. HoD (Leela) opens topic mapping requests, inspects provider categories and confirms
   one canonical topic with rationale/source. Under Annual topic quotas configure the
   topic/year and publish a finite cap. Admin can maintain topic aliases, not approve
   departmental mappings merely by holding Admin authority.
3. Faculty opens Application admission, records truthful declarations, saves a draft,
   reviews the dated source/topic/year/cap facts and submits. Inspect exactly one HELD
   seat and immutable submission facts. DRC approves, then HoD confirms; a DRC's own
   application skips DRC review and goes directly to HoD. HoD/Principal cannot apply.
4. Accept an exact new provider schedule across July–June. With no destination cap,
   the source remains counted and a transfer case appears. HoD follows the case's
   target quota link, publishes/increases capacity, and rechecks (or the worker does).
   Current pool moves once; original submission year and balanced ledger remain.
5. A lawful withdrawal before commencement with no external enrollment releases the
   current pool once, including after transfer. Post-start withdrawal retains count.
   Enrolled-before-start Q04 release is blocked until its verification workflow exists.
6. Principal may inspect institution-wide academic records without write controls.
   Admin source status/observations are distinct from academic authority or credit.

## Person-specific hall-ticket scheduled dates

Faculty records an unverified schedule claim on their application. Current department
HoD may independently authenticate the person's official hall ticket under the
confirmed 2026-11-18 clarification. Inspect the exact person and offering; record the
source archive reference, SHA-256 of the authentic original, source observation time,
scheduled date, rationale and explicit authentication confirmation. Never invent an
archive reference or digest. The original evidence remains in the authorized external
archive: private binary upload/storage is not implemented in this phase.

The finding is MANUAL_HOD_AUTHENTICATED. The server records immutable revision/office
and applies the same capacity-checked transfer to this person only; another person in
the same offering is unaffected. Unverified claims hold transfer for review. Closing
an allocation resolves its pending work items without turning a claim into a verified
finding. No actual examination, certificate or annual compliance is inferred.

Institutional policy gaps remain in POLICY_GAPS.md. Target full/unpublished cannot
be bypassed; existing counted topic migration cannot be invented from a new mapping.
