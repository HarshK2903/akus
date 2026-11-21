-- Aggregate-only checks for immutable application files and submitted manifests.
\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT count(*) AS invalid_attachment_bytes FROM application_attachment_revisions
WHERE CASE WHEN scan='REMOVED' THEN content IS NOT NULL
           ELSE content IS NULL OR octet_length(content)<>size_bytes OR encode(sha256(content),'hex')<>digest END;
SELECT count(*) AS discontinuous_attachment_histories FROM (
  SELECT application_id, series_id FROM application_attachment_revisions GROUP BY application_id,series_id
  HAVING min(version)<>1 OR max(version)<>count(*) OR NOT bool_or(version=1 AND id=series_id)
) invalid;
SELECT count(*) AS inconsistent_submission_attachments FROM application_submissions s
CROSS JOIN LATERAL jsonb_array_elements_text(s.facts->'attachment_revision_ids') ref(id)
LEFT JOIN application_attachment_revisions r ON r.id::text=ref.id AND r.application_id=s.application_id
WHERE r.id IS NULL OR r.scan='REMOVED' OR r.recorded_at>s.submitted_at;
SELECT count(*) AS incomplete_attachment_audits FROM application_attachment_revisions r
WHERE NOT EXISTS (
  SELECT 1 FROM academic_events e WHERE e.entity_id=r.id AND e.actor_id=r.actor_id
  AND e.kind=CASE WHEN r.scan='REMOVED' THEN 'APPLICATION_EVIDENCE_REMOVED' ELSE 'APPLICATION_EVIDENCE_UPLOADED' END
  AND e.data->>'application_id'=r.application_id::text AND e.data->>'digest'=r.digest);
COMMIT;
