# Institutional Google sign-in acceptance

**External gate open. Zero of five participants verified.** On 21 November 2026 the existing public origin was `http://127.0.0.1:8080`, demo mode was enabled, and Google credentials were unconfigured. The API and browser were reachable. Generated signatures exercised the OIDC protocol in tests. No participant used Google to sign in during this audit. [Runtime observation](system-audit-integrations.txt) · [Protocol tests](../../apps/api/tests/test_identity.py)

| Intended participant | Intended office for UAT | Authorized journey after genuine sign-in | Status |
|---|---|---|---|
| faculty-harsh1.cse24@cmrit.ac.in | Faculty | Open personal applications, evidence and compliance. Verify that department approval is unavailable. | BLOCKED — awaiting roster, client and participation |
| hod-ankit.cse24@cmrit.ac.in | HoD | Read department pool and review queue. Verify applicant exemption and department scope. | BLOCKED — awaiting roster, client and participation |
| DRC-awanish.cse24@cmrit.ac.in | DRC Head | Inspect own faculty workspace and independent DRC queue. Verify own application routes to a distinct HoD. | BLOCKED — awaiting roster, client and participation |
| admin-harsh.cse24@cmrit.ac.in | Admin | Read provisioned staff and staged source records. Check that Admin alone cannot approve an academic application. | BLOCKED — awaiting roster, client and participation |
| principle-nikshay.cse24@cmrit.ac.in | Principal | Open institution-wide read oversight and confirm absence of applicant and ordinary academic decision authority. | BLOCKED — awaiting roster, client and participation |

1. An authorized institutional owner supplies staff identifiers, approved email, employment dates, department and the effective source instrument for each office. Reconcile ambiguity before provisioning. Use the permanent person record across episodes. Use the approved bootstrap process for the first Admin. The five addresses alone confer no permission. Keep the approved roster in restricted institutional storage. [Operator procedure](../GOOGLE_OIDC_SETUP.md) · [Unfilled UAT roster](../fixtures/phase2-uat-roster.json)
2. The Workspace administrator authorizes an institution-owned Web client and consent audience. The operator configures secrets privately, disables demo and selects an authorized non-demo UAT dataset. The local callback for a browser on this host is exactly `http://127.0.0.1:8080/api/v1/auth/google/callback`. For a separate approved HTTPS environment use its exact public origin with the same API path and register that URI with Google. Check the externally visible URL, cookie settings and allowed origin after applying the configuration.
3. Each account holder signs in voluntarily through the Google button in their own browser. They keep passwords and MFA private. Observe the expected office from effective institutional sources, correct identity after redirect and access boundaries. Record actual timestamp, role, operator witness, pass/fail, and a redacted evidence reference in the secure UAT store. A failed link, conflicting staff facts or consent denial must produce the corresponding recovery screen.
4. Refresh the authorized page, sign out, then confirm the prior session loses access. For appointment/access revocation tests use an approved UAT record and the authorized source process. Redact request URLs containing OAuth parameters, session cookies, provider subject and personal records. Never attach tokens, browser storage or raw callback requests to this repository.

Authorization for the five live cases, voluntary participation, Google configuration and evidence sign-off all remain with the institution.

Post-remediation preflight reached the Google discovery and public signing-key endpoints from the running API. The local app still reports demo enabled and Google disabled. Live acceptance remains 0/5. [Observed configuration](remediation-integrations.txt)
