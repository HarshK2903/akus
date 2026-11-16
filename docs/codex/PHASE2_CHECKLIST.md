# Phase 2 completion evidence

Execution source: PHASE2_COMPLETION.md A–H; AGENTS.md; full AKUS_MASTER_SPEC.txt.
2026-11-17: all 2,607 master lines reread in bounded sections (1–119, 120–274,
275–504, 505–731, 732–964, 965–1200, 1201–1423, 1424–1550,
1551–1777, 1778–2008, 2009–2248, 2249–2377, 2378–2484, 2485–2607).
Existing 80-page and Q01–Q50 inventories remain authoritative traceability inputs.
No separate onboarding/provisioning addendum exists in this checkout.

| Requirement | Current evidence / gate |
|---|---|
| A Docker baseline | Existing named volume `akus-local_akus_pg` retained; stack restarted; 45 backend tests passed in isolated `akus_completion_test` database |
| B Google OIDC | In progress: real code flow, state/nonce/PKCE, signature/claims, cookies, CSRF, configuration checks |
| C Controlled linking | In progress: separate email/identity/session records, audited reconciliation and operator bootstrap |
| D Real UAT roster | Five participant cases blocked pending approved roster facts, private Google client configuration and voluntary account-holder action |
| E Source administration | In progress: staged CSV/XLSX imports, immutable correction history, departments/subjects/years/teaching |
| F Role routes | In progress: distinct Faculty/DRC/HoD/Admin/Principal dashboards and honest academic integration pages |
| G Verification | Baseline 45 backend passed; final migration, lint, typing, build, UI, browser and concurrency gates pending |
| H Handoff | Update BUILD_PROGRESS, TEST_RESULTS, traceability, setup and manual UAT after observed verification |

## Implementation boundaries

Identity owns Google exchange, stable issuer/subject links, authenticated sessions and
account requests. People owns effective institutional authority. Sources owns reference
records, authoritative employment/teaching imports and correction history. Dashboards
query these services under current scope. React renders these APIs; it never grants roles.

Order: additive schema → identity/API/security tests → source/import/teaching APIs and
transaction tests → working forms and role routes → Docker/browser/regression gates.
No HTTP provider call occurs inside an open database transaction. Imported teaching
acceptance remains IO-02 POLICY_PENDING; later-phase quota/application/compliance
engines are dependencies, never simulated successful academic decisions.
