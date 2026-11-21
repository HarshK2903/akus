-- Aggregate checks only. A lawful rehire keeps the permanent person and distinct episodes.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT count(*) AS overlapping_employment_episodes
FROM employment_episodes e JOIN employment_episodes other
  ON other.person_id=e.person_id AND e.id<other.id
 AND daterange(e.starts_on,e.ends_before,'[)') && daterange(other.starts_on,other.ends_before,'[)');
SELECT count(*) AS wrong_person_session_bindings FROM (
  SELECT s.episode_id FROM institutional_sessions s JOIN employment_episodes e ON e.id=s.episode_id
  WHERE s.person_id<>e.person_id
  UNION ALL
  SELECT s.episode_id FROM auth_sessions s JOIN employment_episodes e ON e.id=s.episode_id
  JOIN persons p ON p.id=e.person_id WHERE p.demo_identity_id IS DISTINCT FROM s.identity_id
) mismatches;
SELECT count(*) AS incomplete_rehire_audits FROM audit_events a
LEFT JOIN employment_episodes e ON e.id=(a.details->>'entity_id')::uuid
LEFT JOIN employment_episodes prior ON prior.id=(a.details->>'previous_episode_id')::uuid
LEFT JOIN faculty_department_appointments m ON m.id=(a.details->>'membership_id')::uuid
WHERE a.action LIKE 'REHIRE:%' AND (prior.id IS NULL OR e.id IS NULL OR prior.id=e.id
  OR prior.person_id<>e.person_id OR e.person_id IS DISTINCT FROM (a.details->>'person_id')::uuid
  OR m.episode_id IS DISTINCT FROM e.id);
SELECT count(*) AS duplicate_separation_decisions FROM (
  SELECT r.application_id FROM exception_case_events ev JOIN academic_reconciliations r ON r.id=ev.case_id
  WHERE ev.action IN ('Q43','Q44','Q45','Q47') GROUP BY r.application_id HAVING count(*)<>1
) duplicates;
SELECT count(*) AS mismatched_frozen_teaching_sources FROM separation_snapshots s
JOIN permanent_departures d ON d.id=s.departure_id CROSS JOIN LATERAL jsonb_array_elements(s.subjects) item
LEFT JOIN source_revisions r ON r.id=(item->>'teaching_revision_id')::uuid
WHERE item ? 'teaching_revision_id' AND (r.id IS NULL OR r.entity_type<>'teaching_assignments'
  OR r.after->>'episode_id' IS DISTINCT FROM d.episode_id::text
  OR r.after->>'subject_id' IS DISTINCT FROM item->>'subject_id'
  OR r.after->>'starts_on' IS DISTINCT FROM item->>'first_assignment'
  OR r.recorded_at>(item->>'knowledge_cutoff')::timestamptz);
COMMIT;
