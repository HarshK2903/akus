# AKUS — Post-Audit Security Remediation and Institutional Acceptance

## Execution mandate

Act as Principal Software Engineer, Application Security Engineer, DevSecOps Engineer and Test Architect. **Continue the existing AKUS repository; do not create a new app or redo Phases 1–8.** The full-system audit completed local functional and recovery checks, but **production release is NO-GO** pending security findings and external acceptance. Your job is to resolve every locally actionable blocker, accurately document external dependencies, and obtain evidence-based status. Implement and verify fixes, not merely a plan.

### Evidence from the latest reported audit — verify against repository files
- 321 backend tests, 3 frontend tests, 59 Playwright journeys passed.
- 80 specified routes covered.
- 198 discrepancy readings across nine databases were zero.
- Docker/DB running on original persistent PostgreSQL volume at migration `0021_application_files`.
- The audit fixed a department-scope authorization defect for an acting HoD who also held an Admin grant.
- **Two critical advisory matches remain in the PostgreSQL/database container image:** `libxml2` and the Go standard library embedded in `gosu` (as reported; confirm precise CVEs, affected versions and scanner evidence before drawing vulnerability conclusions).
- **Zero out of five real Google account sign-ins have been verified.** Google OAuth configuration, authoritative institutional staff/office records and account-holder participation are pending.
- Live NPTEL certificate-provider verification and deployed malware scanning are not verified.
- Unratified policies include IO-02, Q-51, retrospective topic-mapping revisions, and disposition of indefinitely blocked cross-year quota transfers.

## 1. Recover the exact existing state safely

Read `AGENTS.md`, `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, `docs/codex/FINAL_SYSTEM_AUDIT.md`, the final acceptance report, security review, vulnerability scan output, requirements matrix, relevant Dockerfiles/Compose configurations, and the most recent Git diff/status. Discover actual filenames rather than assuming a missing file exists. Verify the audit evidence and current running services. Preserve local changes. Do not reset databases, delete volumes, clear institutional records or audit histories, or silently re-run destructive seed/bootstrap commands. Do not edit historical migrations already applied; add new migrations when required. Create a durable remediation checklist showing each issue, exact evidence, severity, owner, planned fix and recheck command.

## 2. Priority 1: Remediate the two critical database-image advisories

Inspect the actual scanner output including image name and digest, distro, component versions, advisory/CVE IDs, fixed versions, and match source. Assess whether each finding is a real affected artifact, an advisory match requiring confirmation, or a demonstrable false positive. Do **not** assume harmlessness because `gosu` is a startup utility or because a library is not currently exercised. Do not weaken scanner thresholds, suppress vulnerabilities, remove scanner output, change severity labels or mark a finding as fixed without reliable supporting evidence.

If an upstream patched/compatible PostgreSQL base image and/or patched package/component exists, make minimal changes, pin or otherwise control versions appropriately, build with the existing Compose workflow, re-scan all six images and verify zero unresolved release-blocking vulnerabilities. Preserve PostgreSQL version compatibility and use non-destructive rollout; arrange a verified backup/recovery checkpoint before changes that affect the live database image. Do not alter the data directory major version without a vetted upgrade procedure. Confirm container health, migrations, data integrity, and live workflow smoke tests afterward.

If a patch is unavailable, describe precise CVEs, exploitability uncertainty, supplier advisory, mitigating controls, upgrade path and accountable security-owner decision required. **Leave release NO-GO** unless the institution explicitly authorizes and documents a risk exception; Codex cannot self-approve one.

Store machine-readable and human-readable scan evidence in the normal project QA/report location, with image digests and scan timestamps.

## 3. Priority 2: Complete real Google OIDC acceptance prerequisites

Inspect the existing OIDC code and `docs/GOOGLE_OIDC_SETUP.md`. Identify the exact browser-facing origin, authorized callback URI(s), current environment variable names, secret-handling method, Docker/Caddy forwarding configuration, cookie/security settings and required Google Cloud Workspace/OAuth setup. Verify claims checks, `sub`-based linking, state/nonce/PKCE and backend role authorization from existing tests; fix any genuine gaps.

The following are **intended real-person acceptance-test identities**, not hardcoded authority grants:

| Intended role | Email |
|---|---|
| Faculty | `faculty-harsh1.cse24@cmrit.ac.in` |
| HoD | `hod-ankit.cse24@cmrit.ac.in` |
| DRC Head | `DRC-awanish.cse24@cmrit.ac.in` |
| Admin | `admin-harsh.cse24@cmrit.ac.in` |
| Principal | `principle-nikshay.cse24@cmrit.ac.in` |

Require approved institutional staff/appointment records, then have the respective account holders participate voluntarily in real Google sign-ins. Do not infer roles from email prefix or domain, invent their employee IDs or appointments, impersonate persons, request passwords, or store OAuth credentials in Git or chat. Use existing secure Admin bootstrap/provisioning tools under authorized operator control. Report each account separately as NOT STARTED / BLOCKED / LIVE VERIFIED with traceable test evidence that does not expose personal tokens or secrets. If Google credentials, Workspace access or user presence are unavailable, prepare exact human setup instructions and **continue other work**. Do not falsely mark real OAuth accepted based on mock-provider tests.

## 4. Priority 3: Deploy and prove evidence malware scanning

Inspect the private evidence upload/replace/download pipeline and existing quarantine states. Implement or complete a supported malware scanning service configuration for the existing Docker development/test stack (for example, an appropriate supported scanner deployment when justified by existing architecture). Enforce file-size/content checks and quarantine until a trustworthy scan result. On scanner unavailability or error, fail closed: do not release unscanned or suspect documents as approved/downloadable evidence. Preserve auditable status transitions and avoid deleting legitimate existing stored evidence merely because it has no scan result. Demonstrate clean-file acceptance, controlled harmless test signature detection, scanner outage behavior, access isolation, and safe retries; do not use real malicious samples. If deployed scanning cannot be fully activated, document external infrastructure/operations blocker and keep gate NO-GO.

## 5. Priority 4: Make provider verification honest and auditable

Inspect NPTEL provider integrations and certificate verification. Distinguish public course metadata fetching from authoritative **individual enrollment, exam or certificate** verification. Do not treat a course preview API response as a verified individual credential. If no authorized reliable provider verification interface exists, retain formal human documentary verification and provenance/audit according to confirmed institutional policy, explicitly noting that live provider verification remains unverified. Do not scrape private accounts, bypass authentication or fabricate provider verification.

## 6. Preserve boundaries for policies not yet ratified

Keep IO-02 teaching-assignment confirmation, Q-51 reuse of one Silver certificate across subject obligations, retroactive mapping changes for existing allocations, and indefinitely blocked transfer final resolution explicitly `POLICY_PENDING`. Do not make up binding decisions. Preserve draft/read-only/hold states already defined and implement only policy-independent UI and safety improvements. Prepare a concise decision register for the institutional owner with consequences and options, without choosing on their behalf.

## 7. Re-run cross-phase acceptance and release gates

After each targeted fix, run the corresponding focused tests; after all achievable fixes, run the full non-destructive acceptance checks: Python backend, frontend, Playwright, accessibility, Ruff, mypy, ESLint, TypeScript, Prettier, production builds, migration schema drift, Docker health, recovery, authorization matrix and DB/quota/compliance reconciliation. Verify existing critical regressions including acting-HoD+Admin department scope, file evidence isolation, application/approval routes, exactly-once quota release, cross-year transfers, separation cases, and historical reporting. Preserve the current PostgreSQL volume and audit ledger. Do not weaken assertions, skip tests, claim unexecuted checks as passing, or use destructive Compose commands such as `down -v`.

## 8. Artifacts, handoff and stopping rules

Update `BUILD_PROGRESS.md`, `TEST_RESULTS.md`, the final audit/acceptance checklist, requirements coverage matrix, security remediation report and external owner-action list after each verified milestone. Add a durable file such as `docs/qa/RELEASE_BLOCKERS.md` containing each gate, last test evidence, owner, exact next step, and `PASS / FAIL / EXTERNAL_BLOCKED / POLICY_PENDING / UNVERIFIED` status. Keep findings and evidence source paths precise.

Your final summary must clearly state: what you changed, which tests you actually ran, which critical advisories remain unresolved, image digests and scanner outcome, real Google sign-in count out of five, malware scanning status, provider-verification status, unratified policies, and an honest **GO / NO-GO**. Production release remains NO-GO while critical unresolved security findings or required external acceptances remain open. Do not deploy to production or treat local test success as institutional authorization.

**BEGIN NOW**: inspect the present repository and last audit evidence, fix locally actionable security defects first, run tests, and record exact external actions required of me or institutional administrators. Do not stop at planning.
