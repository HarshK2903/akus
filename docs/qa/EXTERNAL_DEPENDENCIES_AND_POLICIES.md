# External dependencies and policy decisions

The phase audit below records its original checkpoint. Subsequent database-image, local scanner and integration results are in the [post-audit remediation report](POST_AUDIT_REMEDIATION_REPORT.md) and [current blocker register](RELEASE_BLOCKERS.md).

Status on 21 November 2026. Confirmed precedence starts with A01–A08 and the V2.4 mapping amendment. Two later recorded decisions designate the current independent department HoD/acting HoD for the specific hall-ticket date and Q19/Q20 enrollment date. Neither decision confers general certificate, subject relevance or integrity authority. [Master](../spec/AKUS_MASTER_SPEC.txt#L1398) · [Hall-ticket ruling](../policy/HALL_TICKET_AUTHORITY_2026-11-18.md) · [Enrollment ruling](../policy/ENROLLMENT_AUTHORITY_2026-11-19.md)

| Dependency | Locally observed or enforced | Evidence needed to close | Responsible party |
|---|---|---|---|
| Google and official identity sources | Demo isolated from Google. Stable subject linking, ambiguous link rejection, employment checks and session revocation have local coverage. | Approved client, registered callback, current authoritative records, five voluntary successful role checks | Workspace administrator, HR and account holders |
| Public NPTEL metadata | Exact offering public preview retrieved with source digest. Scoped synchronization records observations. Acceptance of a changed source requires the authorized action. | Monitor real provider schema, freshness and availability. Source changes need reconciliation. | Catalog operator |
| Personal external enrollment, exam or certificate | A public catalog response supplies course facts. Private evidence remains a claim until an independent finding with the appropriate mandate. | Real approved verification channel or documentary source, scoped designation and successful case acceptance. Score-sharing declarations require separate admissible proof where demanded. | Institution and issuing provider |
| Malware scanning | Quarantine and fail-closed reads exercised with no socket, and clean delivery exercised with a test socket responder. No deployed clamd socket present. | Provision maintained clamd and signatures. Connect its private socket using the [Compose override](../../compose.clamd.yaml). Verify authenticated submit, quarantine, scan, clean delivery, rejected file and outage handling. | Security/operations |
| Production hosting and data governance | Loopback Compose demo and synthetic logical restores verified. | Approved hosting, TLS, managed secrets and access, monitoring, retention, recovery objectives, backup custody and witnessed restore | IT, security and data owner |

[Observed integration configuration and public fetch](system-audit-integrations.txt) · [Google acceptance roster and procedure](GOOGLE_REAL_USER_UAT.md) · [Risk review](SECURITY_REVIEW.md)

| Decision | Safe current effect | Institution must ratify |
|---|---|---|
| IO-02 | Official teaching allocations are recorded. General obligation activation remains pending. An existing admissible archived adjudication can be used for its exact scope. | Who accepts an allocation for assessment and what source activates it |
| Q51 / P-51 | First unambiguous subject assessment can proceed under its rules. Subsequent reuse for a distinct subject waits. | Whether and under what conditions a single certificate fulfills multiple subject obligations |
| P-NEW-07/11 | Use the versioned HoD-approved primary topic on new submissions. Flag impact and preserve existing counted pools. | Retrospective movement or review after a mapping/taxonomy change |
| P-NEW-10 | Capacity-checked cross-year transfer keeps the source counted when the target is unavailable. Capacity events can trigger a recheck. | Final remedy and any priority when the target remains full or unpublished |
| General evidence, P-52/57/58 | Only ratified HoD powers or a documented effective independent case designation permit the corresponding finding. Pending cases preserve evidence and seats under the relevant rule. | Institutional verification mandates, evidence standards and conflict-free fallback |
| P-NEW-04/05/06, P-55/60 | Ordinary hierarchy and current office exemptions apply. Ambiguous transitions and exceptional dispositions await governance. | Emerging technology authority, leave/proration and unfinished cases when offices change |
| P-53/54/56/59/64 | Versioned observations and original deadlines survive corrections. Unknown date precision stays explicit. | Official report reissue, leap-day anniversary, ambiguous same-day exams and corrections to finalized closures |
| P-NEW-03/08, P-61/62/65/66 and identity reconciliation | Explicit quota publication, source corrections and stable identities preserve audit history. | Any new default quota, taxonomy/identity merges, form and retention policy, waivers and signed reporting |

The full decision register retains individual source questions and safe behavior. [Policy gaps](../../POLICY_GAPS.md) · [Historical policy register](../POLICY_REGISTER.md) · [Current acceptance matrix](FINAL_REQUIREMENTS_MATRIX.md)

Infrastructure security owns the remaining high and critical release image advisories and must supply a patched build or a documented risk decision before institutional deployment. [Image scan](system-audit-image-advisories.md) · [Security review](SECURITY_REVIEW.md)

## Post-remediation owner actions

- Workspace administrator registers the exact callback and stores the approved Web client credentials privately. HR supplies authoritative permanent staff identifiers, current employment and effective appointments. The authorized operator selects the separate non-demo UAT dataset and uses the roster-backed first-Admin bootstrap. Each of the five holders signs in independently, demonstrates the allowed and denied actions, signs out and supplies a redacted witness reference. [Setup](../GOOGLE_OIDC_SETUP.md) · [Per-person status](GOOGLE_REAL_USER_UAT.md)
- The registrar identifies the issuing channel or obtains original person-specific documentary proof. Record the permanent person, offering, certificate or enrollment identifier, observation time and original precision, source reference and document digest. Supply the dated appointment for the independent reviewer with the appropriate case and subject scope. A course preview can support catalog dates. An authorized individual finding is still required. [Public-source observation](remediation-integrations.txt)
- The institutional security and infrastructure owners review the remaining image matches, qualify a supplier patch or compatible platform and rehearse restoration before rollout. Only the accountable institution can sign a time-limited risk exception. Record scope, controls, owner, expiry and retest trigger. Production scanning requires signature-age and failure alerts, private socket access, egress controls and a witnessed test on the intended host. [Release blockers](RELEASE_BLOCKERS.md)
- The policy authority supplies dated decisions for the scenarios in the table above, including IO-02, Q51, retrospective remapping and indefinitely blocked transfers. Include the decision maker, affected records, effective date, appeal path and treatment of existing audit history. Preserve existing holds until each decision takes effect.
