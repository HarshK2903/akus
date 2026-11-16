# Domain model boundary

Current implemented schema: DB_ERD.md. Target domains and transaction contracts: ARCHITECTURE.md and implementation-plan.md; complete required model: master specification section 6, lines 1807–1886.

Course category, canonical course, offering, primary quota topic, local teaching subject and certificate achievement are distinct identities. Application, allocation, participation and compliance are distinct state machines. New submissions must atomically reserve from the published department/topic/scheduled-exam-year pool. Actual exam year determines final compliance. No such application command is exposed in Phase 1.

Phase 2A now implements permanent people, episodes/home assignments and effective office/Admin grants as separate source concepts. Source-record changes are transactional and audited; eligibility/access are resolved currently. No application, compliance or quota side effect is inferred from office creation/end. See ADRs.md and POLICY_GAPS.md for transition/chronology boundaries.
