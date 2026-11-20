-- Read-only Phase 6 reconciliation. No staff identities or private document contents are returned.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT count(*) AS discontinuous_credential_histories
FROM (SELECT application_id FROM credential_events GROUP BY application_id
      HAVING min(version) <> 1 OR max(version) <> count(*)) AS gaps;
SELECT count(*) AS incorrect_document_digests FROM credential_documents
WHERE encode(sha256(content), 'hex') <> digest;
SELECT count(*) AS wrong_document_application FROM credential_events e
JOIN credential_documents d ON d.id = e.document_id WHERE e.application_id <> d.application_id;
SELECT count(*) AS incorrect_credential_designations FROM credential_events e
JOIN applications a ON a.id = e.application_id LEFT JOIN credential_mandates m ON m.id = e.mandate_id
WHERE e.kind <> 'ASSERTED' AND (m.id IS NULL OR m.reviewer_id <> e.actor_id OR m.application_id <> a.id
 OR e.actor_id = a.person_id OR e.recorded_at < m.valid_from OR e.recorded_at >= m.valid_until
 OR m.revoked_at <= e.recorded_at);
SELECT count(*) AS conflicting_archive_identities FROM credential_identities i
JOIN historical_certificate_findings h USING (certificate_key) WHERE h.application_id <> i.application_id;
SELECT count(*) AS duplicate_annual_allocations FROM (
 SELECT s.id, event_id FROM compliance_snapshots s CROSS JOIN LATERAL jsonb_array_elements(s.facts->'annual') y
 CROSS JOIN LATERAL jsonb_array_elements_text(y->'allocations') event_id GROUP BY s.id,event_id HAVING count(*) > 1
) duplicates;
SELECT count(*) AS repeated_distinct_subject_credit FROM (
 SELECT s.id, subject->>'allocation' FROM compliance_snapshots s CROSS JOIN LATERAL jsonb_array_elements(s.facts->'silver') subject
 WHERE subject->>'allocation' IS NOT NULL GROUP BY s.id,subject->>'allocation' HAVING count(DISTINCT subject->>'subject_id') > 1
) duplicates;
COMMIT;
