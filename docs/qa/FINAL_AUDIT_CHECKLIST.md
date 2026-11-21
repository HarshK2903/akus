# Final full-system acceptance checklist

The phase audit below records its original checkpoint. Subsequent database-image, local scanner and integration results are in the [post-audit remediation report](POST_AUDIT_REMEDIATION_REPORT.md) and [current blocker register](RELEASE_BLOCKERS.md).

21 November 2026. This checklist implements the repository’s final audit instructions across Phases 1–8. Historical failures are retained with their repaired gates. Package findings and real-world acceptance have independent decisions. [Audit instructions](../codex/FINAL_SYSTEM_AUDIT.md) · [Detailed requirements matrix](FINAL_REQUIREMENTS_MATRIX.md)

| Decision | Scope | Witness or next decision |
|---|---|---|
| VERIFIED PASS | Interrupted combined and browser runs finished. Read the log through the production build and verified all 219 inputs before editing. Python inspected the mobile PNG after optional ImageMagick was unavailable. | [Recovery evidence](system-audit-interruption.txt) · [Recovered suite](system-audit-acceptance-checks.txt) |
| VERIFIED PASS | PostgreSQL, API, frontend, proxy and worker recovered on the original volume. Cluster identity and institutional aggregate counts matched across the patch rollout. | [Before](system-audit-storage-before.txt) · [After](system-audit-storage-after.txt) · [Stack start](system-audit-patched-start.txt) |
| VERIFIED PASS | Google code flow and stable subject linking with controlled signed fixtures, first Admin, effective-dated roster/office changes, CSV/XLSX validation and rehire. | [Identity tests](../../apps/api/tests/test_identity.py) · [People and source coverage](FINAL_REQUIREMENTS_MATRIX.md) |
| VERIFIED PASS | Distinct DRC and HoD, faculty two-stage approval, DRC own direct-HoD route, HoD/Principal exemption, Principal read oversight and scoped Admin access. Transfer inbox and detail check the acting office even when the actor holds an additional Admin grant. | [Regression](../../apps/api/tests/test_admission.py#L393) · [Five-role journeys](system-audit-patched-browser.txt) |
| VERIFIED PASS | Canonical courses and offerings, HoD topic mapping, July–June pools, one reservation at submission, capacity-limited transfers, held source on failure, current-pool release and concurrent terminal decisions. | [Admission tests](../../apps/api/tests/test_admission.py) · [Final ledger checks](system-audit-closeout-ledgers.txt) |
| VERIFIED PASS | Enrollment precision, withdrawal, prior-result verification, no-repeat, HR separation chronology, split authority, integrity hold/invalidation, rehire and audit. | [Policy-by-policy witnesses](FINAL_REQUIREMENTS_MATRIX.md) · [Isolated real-DB browser cases](system-audit-patched-isolated.txt) |
| VERIFIED PASS | Authorized synthetic certificate decisions, exam-year annual pathways, 75% subject Silver, source timing, independently versioned as-of assessments and immutable evidence references. | [Compliance](../../apps/api/tests/test_compliance.py) · [Exception cases](../../apps/api/tests/test_exception_cases.py) |
| VERIFIED PASS | CSRF, Origin, cookie/session controls, private uploads and downloads, quarantined responses, access-filtered search and anonymous denial for all 114 protected operations. | [Security review](SECURITY_REVIEW.md) · [Workspace contracts](../../apps/api/tests/test_workspace.py) |
| VERIFIED PASS | 80 blueprint routes. Five public entries, 51 fixed protected paths and 24 parameterized pages received browser coverage. Standard and isolated workflows include mobile widths, keyboard, axe, reload, decisions and error handling. | [Standard](system-audit-patched-browser.txt) · [Record pages](system-audit-patched-records.txt) · [Isolated](system-audit-patched-isolated.txt) |
| VERIFIED PASS | Actual Orca speech generation for focused login and recovery controls in Chromium. Synthetic keyboard interaction and screen-reader output were observed on the virtual display. | [Four generated utterances](system-audit-screen-reader.txt) |
| VERIFIED PASS | Deduplication, retry/backoff, worker heartbeat and recovery. Synthetic database restore with private manifests, retained history and discrepancy queries. | [Job tests](../../apps/api/tests/test_workspace.py) · [Restore procedure](../../scripts/check-test-restore.sh) |
| VERIFIED PASS | Python and web lint, format, typechecks, builds and local regression suites. Config-only validation passed for the optional scanner socket overlay. | [Patched-image quality gate](system-audit-patched-checks.txt) · [Scanner configuration](../../compose.clamd.yaml) |
| VERIFIED FAILURE | Release images still match high/critical advisories after OS and packaging fixes. Two critical matches remain on the DB image. The package findings are observed. Runtime exploitability was not established. | Infrastructure security must qualify upstream fixes or record an approved risk decision. [Before/after scan](system-audit-image-advisories.md) |
| BLOCKED BY EXTERNAL CONFIGURATION | Zero of five live Google sign-ins. Approved client, official appointments, non-demo UAT configuration and voluntary account-holder participation required. | [Per-account checklist](GOOGLE_REAL_USER_UAT.md) |
| BLOCKED BY EXTERNAL CONFIGURATION | A real public provider preview was observed. Private enrollment/certificate authentication and a deployed clamd engine with current signatures still require institutional provisioning and witnessed acceptance. | [Observed integrations](system-audit-integrations.txt) · [External owner actions](EXTERNAL_DEPENDENCIES_AND_POLICIES.md) |
| BLOCKED BY UNCONFIRMED POLICY | IO-02, Q51, retrospective topic changes, indefinite failed-transfer remedies, general verification designations and other recorded policy decisions. | Institutional policy authority provides a dated ruling or scoped designation. [Decision backlog](EXTERNAL_DEPENDENCIES_AND_POLICIES.md) |
| NOT YET TESTED | Production TLS and real identity-provider round trip, institutional PITR against signed RPO/RTO, real-user assistive-technology acceptance, and production demand/load. Local restore, timings and accessibility checks have their own evidence. | [Production readiness](RELEASE_READINESS_GATE.md) |

**Decision.** Engineering acceptance applies to the executed local workflows. Production release is NO-GO while the security, configuration, governance and institutional acceptance gates remain open.

## Post-audit release recheck

| Result | Scope and evidence |
|---|---|
| VERIFIED PASS | The gosu critical is cleared in the rebuilt PostgreSQL image. The tested restore reproduced audit and evidence manifests. [Restore](remediation-candidate-restore.txt) |
| VERIFIED PASS | The deployed local ClamAV engine passed both private file workflows, including outage, role denial, fresh signatures and immutable recovery. [Executed tests](remediation-final-scanner.txt) |
| VERIFIED FAILURE | Trixie libxml2 remains critically affected. Additional high matches remain in six images. [Seven-image inventory](remediation-image-scans.md) |
| BLOCKED BY EXTERNAL CONFIGURATION | Five Google sign-ins, private NPTEL case acceptance, production scanner and intended deployment sign-off. [Owner checklist](RELEASE_BLOCKERS.md) |
| BLOCKED BY UNCONFIRMED POLICY | IO-02, Q51, retrospective remapping, indefinitely blocked transfer disposition and remaining mandates. [Institutional decisions](EXTERNAL_DEPENDENCIES_AND_POLICIES.md) |

The post-remediation regression and integrity gates passed with 331 backend, two real-engine, three frontend and 60 browser tests and 242 zero discrepancy readings. [Post-audit acceptance](POST_AUDIT_REMEDIATION_REPORT.md)
