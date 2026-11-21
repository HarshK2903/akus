"""Paged institutional reads over authoritative domain ledgers.

All fragments below are static application SQL. User input is always a bound value.
Each register projects a stable record, human-readable context and authorized drilldown.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.workspace import personal

APPLICATIONS = """
SELECT a.id, c.title, concat_ws(' · ', p.display_name,d.name,o.provider_id,t.name,y.label,
  'Quota '||l.state,'Next '||a.next_office,
  (SELECT string_agg(r.stage||' '||r.decision||' '||to_char(r.recorded_at AT TIME ZONE 'Asia/Kolkata','YYYY-MM-DD HH24:MI')||' IST',', ' ORDER BY r.recorded_at) FROM application_review_decisions r WHERE r.application_id=a.id),
  (SELECT string_agg(rc.reason,', ' ORDER BY rc.kind) FROM academic_reconciliations rc WHERE rc.application_id=a.id AND rc.status='OPEN')) AS context, a.state AS status,
  coalesce(a.submitted_at,a.created_at) AS recorded_at, '/app/applications/'||a.id AS href,
  a.department_id, q.academic_year_id, q.topic_id
FROM applications a JOIN nptel_courses c ON c.id=a.course_id JOIN persons p ON p.id=a.person_id
JOIN departments d ON d.id=a.department_id JOIN nptel_offerings o ON o.id=a.offering_id
LEFT JOIN quota_allocations l ON l.application_id=a.id LEFT JOIN department_topic_quotas q ON q.id=l.pool_id
LEFT JOIN nptel_topics t ON t.id=q.topic_id LEFT JOIN academic_years y ON y.id=q.academic_year_id
"""
DECISIONS = """
SELECT r.id,c.title,concat_ws(' · ',s.display_name,p.display_name,r.stage,'Current '||a.state,r.facts->>'reason') AS context,
r.decision AS status,r.recorded_at,'/app/applications/'||a.id||'/history' AS href,a.department_id
FROM application_review_decisions r JOIN applications a ON a.id=r.application_id
JOIN nptel_courses c ON c.id=a.course_id JOIN persons p ON p.id=r.actor_id JOIN persons s ON s.id=a.person_id
WHERE a.department_id=ANY(CAST(:scopes AS uuid[])) AND r.stage=ANY(CAST(:stages AS text[]))
"""
HOD_HISTORY = """
UNION ALL SELECT r.id,t.name,concat_ws(' · ',p.display_name,r.reason,'Cap '||r.maximum),r.status,r.recorded_at,
'/hod/quotas/'||q.id||'/ledger',q.department_id FROM topic_quota_revisions r JOIN department_topic_quotas q ON q.id=r.pool_id
JOIN persons p ON p.id=r.actor_id JOIN nptel_topics t ON t.id=q.topic_id WHERE q.department_id=ANY(CAST(:scopes AS uuid[]))
UNION ALL SELECT r.id,c.title,concat_ws(' · ',t.name,p.display_name,r.reason),'TOPIC_MAPPING',r.valid_from,
'/hod/topic-mappings/'||m.course_id||'?department='||m.department_id,m.department_id
FROM primary_topic_mapping_revisions r JOIN department_course_mappings m ON m.id=r.mapping_id
JOIN nptel_courses c ON c.id=m.course_id JOIN persons p ON p.id=r.actor_id JOIN nptel_topics t ON t.id=r.topic_id
WHERE m.department_id=ANY(CAST(:scopes AS uuid[]))
UNION ALL SELECT e.id,c.title,concat_ws(' · ',p.display_name,e.facts->>'reason'),e.action,e.recorded_at,
'/hod/separation-cases/'||rc.id,a.department_id FROM exception_case_events e JOIN academic_reconciliations rc ON rc.id=e.case_id
JOIN applications a ON a.id=rc.application_id JOIN nptel_courses c ON c.id=a.course_id JOIN persons p ON p.id=e.actor_id
WHERE rc.kind='SEPARATION' AND e.office_id IS NOT NULL AND a.department_id=ANY(CAST(:scopes AS uuid[]))
UNION ALL SELECT f.id,c.title,concat_ws(' · ',p.display_name,f.reason,f.source_reference),f.outcome,f.recorded_at,
'/hod/outcome-verifications/'||a.id,a.department_id FROM outcome_findings f JOIN nptel_attempts a ON a.id=f.attempt_id
JOIN nptel_courses c ON c.id=a.course_id JOIN persons p ON p.id=f.actor_id WHERE a.department_id=ANY(CAST(:scopes AS uuid[]))
"""
DEPARTMENTS = """
SELECT d.id,d.name AS title,concat_ws(' · ',d.code,'HoD '||coalesce(staff.hod,'vacant'),
'DRC '||coalesce(staff.drc,'vacant'),(SELECT count(*) FROM applications a WHERE a.department_id=d.id AND a.state='UNDER_REVIEW')||' pending reviews',
(SELECT count(*) FROM department_topic_quotas q WHERE q.department_id=d.id AND q.status='PUBLISHED' AND q.occupied=q.maximum AND (CAST(:pool_year AS uuid) IS NULL OR q.academic_year_id=CAST(:pool_year AS uuid)))||' full pools',
(SELECT count(*) FROM faculty_department_appointments da JOIN employment_episodes e ON e.id=da.episode_id
 JOIN persons pp ON pp.id=e.person_id WHERE da.department_id=d.id AND e.is_faculty AND pp.enabled
 AND daterange(da.starts_on,da.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
 AND daterange(e.starts_on,e.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
 AND NOT EXISTS(SELECT 1 FROM office_appointments o WHERE o.person_id=pp.id AND NOT o.superseded AND o.office IN ('HOD','ACTING_HOD','PRINCIPAL')
 AND tstzrange(o.valid_from,o.valid_until,'[)') @> now()))||' eligible faculty') AS context,
'DEPARTMENT' AS status,NULL::timestamptz AS recorded_at,'/principal/departments/'||d.id AS href,d.id AS department_id
FROM departments d LEFT JOIN LATERAL (
SELECT max(p.display_name) FILTER(WHERE o.office IN ('HOD','ACTING_HOD')) hod,
max(p.display_name) FILTER(WHERE o.office='DRC_HEAD') drc FROM office_appointments o JOIN persons p ON p.id=o.person_id
WHERE o.department_id=d.id AND NOT o.superseded AND o.valid_from<=now() AND (o.valid_until IS NULL OR o.valid_until>now())
AND p.enabled AND EXISTS(SELECT 1 FROM employment_episodes e WHERE e.person_id=p.id
 AND daterange(e.starts_on,e.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date)
) staff ON true
"""
QUOTAS = """
SELECT q.id,t.name AS title,concat_ws(' · ',d.name,y.label,q.occupied||' of '||q.maximum||' seats') AS context,
q.status,q.published_at AS recorded_at,'/hod/quotas/'||q.id||'/ledger' AS href,q.department_id,q.academic_year_id,q.topic_id
FROM department_topic_quotas q JOIN nptel_topics t ON t.id=q.topic_id JOIN departments d ON d.id=q.department_id
JOIN academic_years y ON y.id=q.academic_year_id
"""
MAPPINGS = """
SELECT r.id,c.title,concat_ws(' · ',d.name,t.name,r.source_reference,'Revision '||r.version),
'CURRENT',r.valid_from,'/hod/topic-mappings/'||m.course_id||'?department='||d.id,m.department_id,NULL::uuid,r.topic_id
FROM primary_topic_mapping_revisions r JOIN department_course_mappings m ON m.id=r.mapping_id
JOIN nptel_courses c ON c.id=m.course_id JOIN departments d ON d.id=m.department_id JOIN nptel_topics t ON t.id=r.topic_id
WHERE r.valid_until IS NULL
"""
CASES = """
SELECT rc.id,c.title AS title,concat_ws(' · ',d.name,rc.kind,rc.reason) AS context,rc.status,rc.updated_at AS recorded_at,
CASE rc.kind WHEN 'INTEGRITY' THEN '/hod/integrity/'||rc.id WHEN 'SEPARATION' THEN '/hod/separation-cases/'||rc.id
WHEN 'QUOTA_TRANSFER' THEN '/hod/quota-transfers/'||rc.id ELSE '/app/applications/'||a.id END AS href,a.department_id
FROM academic_reconciliations rc JOIN applications a ON a.id=rc.application_id JOIN departments d ON d.id=a.department_id
JOIN nptel_courses c ON c.id=a.course_id
UNION ALL SELECT r.id,c.title,concat_ws(' · ',d.name,'Primary mapping required',r.reason),r.status,r.created_at,
'/hod/topic-mappings/'||c.id||'?department='||r.department_id,r.department_id FROM primary_topic_mapping_requests r
JOIN nptel_courses c ON c.id=r.course_id JOIN departments d ON d.id=r.department_id WHERE r.status='REVIEW_PENDING'
UNION ALL SELECT a.id,c.title,concat_ws(' · ', d.name, a.next_office,'Independent office required'),'VACANT_OFFICE',a.submitted_at,
'/app/review-office-alerts',a.department_id FROM applications a JOIN departments d ON d.id=a.department_id JOIN nptel_courses c ON c.id=a.course_id
WHERE a.state='UNDER_REVIEW' AND NOT EXISTS(SELECT 1 FROM office_appointments o JOIN persons p ON p.id=o.person_id
JOIN employment_episodes e ON e.person_id=p.id JOIN faculty_department_appointments da ON da.episode_id=e.id
WHERE o.department_id=a.department_id AND o.office_group=a.next_office AND NOT o.superseded AND p.enabled AND p.id<>a.person_id
AND tstzrange(o.valid_from,o.valid_until,'[)') @> now() AND daterange(e.starts_on,e.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date
AND daterange(da.starts_on,da.ends_before,'[)') @> (now() AT TIME ZONE 'Asia/Kolkata')::date)
"""
AUDIT = """
SELECT ev.id,ev.action AS title,concat_ws(' · ',ev.details->>'entity_id',ev.details->>'application_id',
ev.details->>'actor_person_id',ev.details->>'office_id',ev.details->>'authority',ev.details->>'policy') AS context,
'AUDIT' AS status,ev.recorded_at,NULL::text AS href,NULLIF(ev.details->>'department_id','') AS department_id
FROM audit_events ev
"""
ADMIN_AUDIT = """
SELECT r.id,r.entity_type AS title,concat_ws(' · ',r.entity_id,r.context->>'source_reference',r.context->>'reason',
r.context->>'actor_person_id',
CASE WHEN r.entity_type='employment_episodes' THEN concat('Period ',r.before->>'starts_on',' → ',r.after->>'starts_on',', ends ',r.after->>'ends_before') END) AS context,
CASE WHEN r.before IS NULL THEN 'CREATED' ELSE 'REVISED' END AS status,r.recorded_at,
CASE r.entity_type WHEN 'persons' THEN '/admin/staff/'||r.entity_id
WHEN 'employment_episodes' THEN '/admin/staff/'||(r.after->>'person_id')||'/employment'
WHEN 'teaching_assignments' THEN '/people/teaching/'||r.entity_id END AS href,NULL::uuid AS department_id
FROM source_revisions r
UNION ALL SELECT id,action,concat_ws(' · ',details->>'job_id',details->>'actor_person_id'),'OPERATIONS',
recorded_at,NULL,NULL FROM audit_events WHERE action IN ('WORK_RETRIED','NOTIFICATION_TEMPLATE_CHANGED','NOTIFICATION_TEST_SENT','UNKNOWN_WORK_KIND','WORK_FAILED','REGISTER_EXPORTED','PROVIDER_REFRESH_QUEUED','PROVIDER_REFRESH_RESULT','PROVIDER_SOURCE_FLAGGED')
"""
OPERATIONS = """
SELECT id,kind AS title,concat_ws(' · ',key,'Attempts '||attempts,last_error,'Next attempt '||next_attempt_at) AS context,
state AS status,created_at AS recorded_at,NULL::text AS href,NULL::uuid AS department_id,attempts FROM work_jobs
"""


def allowed(actor: Actor, role: str) -> None:
    if role not in actor.roles:
        raise HTTPException(403, "REGISTER_SCOPE_DENIED")


def fetch(
    db: Session,
    actor: Actor,
    report: str,
    *,
    search: str = "",
    status: str = "",
    department: UUID | None = None,
    year: UUID | None = None,
    topic: UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    offset: int = 0,
    limit: int = 25,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "scopes": actor.scopes,
        "offset": offset,
        "limit": limit,
        "person": actor.person.id,
        "principal": "PRINCIPAL" in actor.roles,
        "episode": actor.episode.id,
    }
    if report == "tasks":
        sql = personal.tasks(actor)
    elif report == "search":
        if not search.strip():
            return {"items": [], "total": 0}
        sql = personal.search(actor)
    elif report == "notifications":
        sql = personal.INBOX
    elif report in {"drc-history", "hod-history"}:
        role = "DRC_HEAD" if report == "drc-history" else "HOD"
        allowed(actor, role)
        params["scopes"] = [
            o.department_id
            for o in actor.offices
            if o.office in (("DRC_HEAD",) if role == "DRC_HEAD" else ("ACTING_HOD", "HOD"))
        ]
        params["stages"] = ["DRC_HEAD"] if role == "DRC_HEAD" else ["HOD", "ACTING_HOD"]
        sql = DECISIONS + (" AND r.actor_id=:person" if role == "DRC_HEAD" else HOD_HISTORY)
    elif report == "department-applications":
        if "PRINCIPAL" not in actor.roles:
            allowed(actor, "HOD")
            params["scopes"] = [
                o.department_id for o in actor.offices if o.office in ("ACTING_HOD", "HOD")
            ]
            sql = (
                APPLICATIONS
                + " WHERE a.department_id=ANY(CAST(:scopes AS uuid[])) AND a.state<>'DRAFT'"
            )
        else:
            sql = APPLICATIONS
    elif report in {"applications", "departments", "topics-quotas", "exceptions", "audit"}:
        allowed(actor, "PRINCIPAL")
        sql = {
            "applications": APPLICATIONS,
            "departments": DEPARTMENTS,
            "topics-quotas": QUOTAS + " UNION ALL " + MAPPINGS,
            "exceptions": CASES,
            "audit": AUDIT,
        }[report]
    elif report in {"operations", "source-audit"}:
        allowed(actor, "ADMIN")
        sql = OPERATIONS if report == "operations" else ADMIN_AUDIT
    else:
        raise HTTPException(404, "REGISTER_NOT_FOUND")
    if report == "departments":
        params["pool_year"] = year
        year = None
    filters = []
    if search.strip():
        filters.append("strpos(lower(concat_ws(' ',id,title,context,status)),lower(:search))>0")
        params["search"] = search.strip()
    if status:
        filters.append("upper(status)=upper(:status)")
        params["status"] = status
    if department:
        filters.append("department_id::text=CAST(:department AS text)")
        params["department"] = str(department)
    for name, value in (("academic_year_id", year), ("topic_id", topic)):
        if value:
            if report not in {"applications", "department-applications", "topics-quotas"}:
                raise HTTPException(422, "FILTER_NOT_APPLICABLE")
            filters.append(f"{name} = :{name}")
            params[name] = value
    for name, timestamp, op in (("since", since, ">="), ("until", until, "<=")):
        if timestamp:
            if not timestamp.tzinfo:
                raise HTTPException(422, "TIMEZONE_REQUIRED")
            filters.append(f"recorded_at {op} :{name}")
            params[name] = timestamp
    relation = (
        " FROM (" + sql + ") register_rows" + (" WHERE " + " AND ".join(filters) if filters else "")
    )
    total = db.scalar(text("SELECT count(*)" + relation), params)
    rows = db.execute(
        text(
            "SELECT *"
            + relation
            + " ORDER BY recorded_at DESC NULLS LAST,title,id LIMIT :limit OFFSET :offset"
        ),
        params,
    ).mappings()
    result: dict[str, Any] = {"items": [dict(row) for row in rows], "total": total}
    if report in {"department-applications", "applications", "tasks"}:
        result["counts"] = dict(
            db.execute(text("SELECT status,count(*)" + relation + " GROUP BY status"), params)
            .tuples()
            .all()
        )
    return result
