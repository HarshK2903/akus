# Domain model boundary

Current implemented schema: DB_ERD.md. Target domains and transaction contracts: ARCHITECTURE.md and implementation-plan.md; complete required model: master specification section 6, lines 1807–1886.

Course category, canonical course, offering, primary quota topic, local teaching subject and certificate achievement are distinct identities. Application, allocation, participation and compliance are distinct state machines. New submissions must atomically reserve from the published department/topic/scheduled-exam-year pool. Actual exam year determines final compliance. The expanded Phase 3 now exposes that admission command with a real allocation ledger.

Phase 2 implements permanent people, episodes/home assignments, effective offices/Admin grants, official email history, immutable external identity links, observed provider-email history, sessions, source imports/revisions and teaching/canonical subjects as separate concepts. Source-record changes are transactional and audited; eligibility/access are resolved currently. Office creation/end queues affected academic cases for reconciliation without inferring withdrawal, exemption or compliance credit. See ADRs.md and POLICY_GAPS.md for transition/chronology boundaries.

Personal scheduled-date findings are independent of provider-wide forecasts, actual
exam evidence and certificate achievements. Current HoD authenticates exact-person
hall-ticket evidence; this can change current charged year but never submission facts
or another applicant. Application closure resolves pending work without verifying it.
