"""Personal task, search and notification projections, filtered before pagination."""

from akus.access import Actor

NOTICES = """
SELECT n.id,coalesce(t.heading,initcap(replace(n.kind,'_',' '))) AS title,c.title AS context,
n.created_at AS recorded_at,'/app/applications/'||a.id AS href,a.department_id
FROM academic_notices n JOIN applications a ON a.id=n.application_id JOIN nptel_courses c ON c.id=a.course_id
LEFT JOIN LATERAL (SELECT heading FROM notice_template_versions WHERE category='APPLICATION'
 AND recorded_at<=n.created_at ORDER BY version DESC LIMIT 1) t ON true WHERE a.person_id=:person OR EXISTS(SELECT 1 FROM academic_events ev JOIN office_appointments office
ON office.id::text=ev.data->>'recipient_office_id' WHERE ev.kind='OFFICE_NOTICE_ARCHIVED' AND ev.entity_id=n.id
AND office.person_id=:person AND NOT office.superseded AND tstzrange(office.valid_from,office.valid_until,'[)') @> now()
AND office.department_id=a.department_id)
UNION ALL SELECT id,heading,'In-app test',recorded_at,NULL,NULL FROM personal_test_notices WHERE person_id=:person
"""
INBOX = (
    """
SELECT n.*,CASE WHEN r.read_at IS NULL THEN 'UNREAD' ELSE 'READ' END AS status FROM (
"""
    + NOTICES
    + """) n LEFT JOIN personal_notice_reads r ON r.notice_id=n.id AND r.person_id=:person
"""
)
COURSES = """
SELECT c.id,c.title,c.code AS context,'COURSE' AS status,NULL::timestamptz AS recorded_at,
'/app/catalog/'||c.id AS href,NULL::uuid AS department_id FROM nptel_courses c
UNION ALL SELECT o.id,o.provider_id,c.title,'OFFERING',NULL,'/app/offerings/'||o.id,NULL
FROM nptel_offerings o JOIN nptel_courses c ON c.id=o.course_id
UNION ALL SELECT id,name,code,'TOPIC',NULL,'/hod/topics/'||id,NULL FROM nptel_topics
"""
APPS = """
SELECT a.id,c.title,concat_ws(' · ',p.display_name,o.provider_id,a.state,a.next_office) AS context,
'APPLICATION' AS status,coalesce(a.submitted_at,a.created_at) AS recorded_at,
'/app/applications/'||a.id AS href,a.department_id FROM applications a JOIN nptel_courses c ON c.id=a.course_id
JOIN persons p ON p.id=a.person_id JOIN nptel_offerings o ON o.id=a.offering_id
"""


def search(actor: Actor) -> str:
    scope = (
        ""
        if set(actor.roles) & {"ADMIN", "PRINCIPAL"}
        else " WHERE a.person_id=:person OR (a.department_id=ANY(CAST(:scopes AS uuid[])) AND a.state<>'DRAFT')"
    )
    staff = """SELECT p.id,p.display_name,p.staff_key,'STAFF',NULL,CASE WHEN p.id=:person THEN '/app/profile' ELSE '/people/staff/'||p.id END,NULL FROM persons p"""
    if not set(actor.roles) & {"ADMIN", "PRINCIPAL"}:
        staff += " WHERE p.id=:person"
        if "HOD" in actor.roles:
            staff += """ OR EXISTS (SELECT 1 FROM employment_episodes e JOIN faculty_department_appointments da ON da.episode_id=e.id
            WHERE e.person_id=p.id AND da.department_id=ANY(CAST(:scopes AS uuid[]))
            AND daterange(e.starts_on,e.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
            AND daterange(da.starts_on,da.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date)"""
    docs = """SELECT d.id,c.title,'Certificate evidence · '||d.scan,'DOCUMENT',NULL,'/app/certificates/'||a.id,a.department_id
    FROM credential_documents d JOIN applications a ON a.id=d.application_id JOIN nptel_courses c ON c.id=a.course_id
    WHERE a.person_id=:person OR (EXISTS(SELECT 1 FROM credential_mandates m WHERE m.application_id=a.id AND m.reviewer_id=:person
    AND m.valid_from<=now() AND m.valid_until>now() AND m.revoked_at IS NULL) AND NOT EXISTS
    (SELECT 1 FROM application_review_decisions r WHERE r.application_id=a.id AND r.actor_id=:person))"""
    # Keep the same visibility as the evidence page. Rank revisions before filtering
    # removals so a removed or replaced filename cannot reappear in search.
    attachments = """SELECT f.id,f.filename,concat_ws(' · ',c.title,f.kind,f.scan),'DOCUMENT',
        f.recorded_at,'/app/applications/'||a.id||'/evidence',a.department_id
        FROM applications a JOIN nptel_courses c ON c.id=a.course_id
        CROSS JOIN LATERAL (SELECT DISTINCT ON (series_id) id,filename,kind,scan,recorded_at
          FROM application_attachment_revisions WHERE application_id=a.id
          ORDER BY series_id,version DESC) f
        WHERE f.scan<>'REMOVED' AND (a.person_id=:person OR (a.state<>'DRAFT' AND
        (:principal OR a.department_id=ANY(CAST(:scopes AS uuid[])))))"""
    return " UNION ALL ".join((COURSES, APPS + scope, staff, docs, attachments))


def tasks(actor: Actor) -> str:
    clauses = (
        ["a.person_id=:person AND a.episode_id=:episode AND a.state='DRAFT'"]
        if actor.view().applicant_eligible
        else []
    )
    if "PRINCIPAL" in actor.roles:
        clauses.append("a.state='UNDER_REVIEW'")
    else:
        for role, office in (("HOD", "HOD"), ("DRC_HEAD", "DRC_HEAD")):
            if role in actor.roles:
                clauses.append(
                    f"a.person_id<>:person AND a.state='UNDER_REVIEW' AND a.next_office='{office}' AND a.department_id=ANY(CAST(:scopes AS uuid[]))"
                )
    sql = (
        APPS.replace("'APPLICATION' AS status", "a.state AS status")
        + " WHERE "
        + " OR ".join(clauses or ["false"])
    )
    if "HOD" in actor.roles:
        sql += """ UNION ALL SELECT r.id,c.title,r.reason,r.status,r.created_at,'/hod/topic-mappings/'||c.id||'?department='||r.department_id,r.department_id
        FROM primary_topic_mapping_requests r JOIN nptel_courses c ON c.id=r.course_id WHERE r.status='REVIEW_PENDING' AND r.department_id=ANY(CAST(:scopes AS uuid[]))"""
    if "HOD" in actor.roles or "PRINCIPAL" in actor.roles:
        sql += """ UNION ALL SELECT r.id,c.title,concat_ws(' · ',d.name,r.reason),r.kind,r.updated_at,
          CASE r.kind WHEN 'SEPARATION' THEN '/hod/separation-cases/' ELSE '/hod/quota-transfers/' END||r.id,a.department_id
          FROM academic_reconciliations r JOIN applications a ON a.id=r.application_id JOIN departments d ON d.id=a.department_id
          JOIN nptel_courses c ON c.id=a.course_id WHERE r.status='OPEN' AND r.kind IN ('SEPARATION','QUOTA_TRANSFER')"""
        if "PRINCIPAL" not in actor.roles:
            sql += " AND a.department_id=ANY(CAST(:scopes AS uuid[])) AND a.person_id<>:person"
    if "ADMIN" in actor.roles:
        sql += """ UNION ALL SELECT id,filename,kind,status,recorded_at,'/admin/imports/'||id,NULL FROM source_imports WHERE status='STAGED'"""
    return sql
