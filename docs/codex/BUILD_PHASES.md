# AKUS Codex phase plan

Use the master specification as the only binding feature source. Maintain requirements-to-page-to-API-to-test traceability. Apply the latest superseding amendments before historical policy lines.

Phase 0 — Inventory and audit. Read both inputs fully in manageable chunks; generate architecture decisions, phase plan, complete 80-page route/role matrix, 50-policy compatibility matrix and unresolved-policy list; inspect current repository; write real acceptance checkpoints.

Phase 1 — Runnable foundation. Compose/dev scripts, PostgreSQL schema + Alembic, FastAPI health/OpenAPI, React + TS + Vite + Router shell, consistent UI tokens, automated checks, local demo identity boundary. Verify frontend/backend/db all run.

Phase 2 — People and access. Institutional identity, staff histories, employment episodes, effective-dated exclusive DRC/HoD appointments, access filtering, five role-specific shells/dashboards, Principal read-only global oversight, safe local login fixtures.

Phase 3 — Course, topic and quota. Canonical courses vs provider offerings, provider snapshots, multi-category canonical topic requests, HoD per-department primary mapping and versioning, HoD annual topic quotas, publication, occupancy, topic/cap unknown draft blocking; migrations and tests.

Phase 4 — Applications and reviews. Faculty/DRC flows, separate DRC-own application path, draft and review pages, chronological enrollment checks, canonical course no-repeat, atomic reservation, DRC/HoD decisions, withdrawal/rejection and policy state machines; concurrency tests.

Phase 5 — Rescheduling and exceptional cases. Verified official cross-year exam-date change, atomic quota transfer and retain+flag on failure, idempotency and audit; authority rotation, deadlines, integrity and chronology reviews. Mapping-revision existing-seat movement is unresolved: do not invent retroactive behavior.

Phase 6 — Evidence and compliance. External enrollment evidence, certificates, exam dates, two annual pathways and separate subject-wise Silver ledger, timelines, reports, failed-attempt verification, accurate retrospective credit and episode-scoped obligations. No fake external verification.

Phase 7 — Employment exits and historical correctness. Separation Q41-Q50, rehire, quota release exceptions, chronology review, retrospective annual/Silver recognition, immutable as-of reporting; exhaustive tests.

Phase 8 — Complete mature UI and QA. Close route gaps through 80-page inventory; audit every route/action/permission, accessible light theme, realistic loading/empty/error states, responsive Playwright tests with screenshots, security review, coverage matrix, deployment docs.

**Definition of done for each phase:** files + migrations/APIs + UI where relevant + tests passing on local environment + a recorded manual demo; blockers explicitly named. None of these phases should be marked complete based on scaffolding alone.
