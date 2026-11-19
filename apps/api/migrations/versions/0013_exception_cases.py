"""Permanent departure evidence, case timelines and constrained closure states."""

from alembic import op

revision = "0013_exception_cases"
down_revision = "0012_prior_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE permanent_departures (
	id UUID NOT NULL, 
	episode_id UUID NOT NULL, 
	effective_on DATE NOT NULL, 
	effective_at TIMESTAMP WITH TIME ZONE, 
	actor_id UUID NOT NULL, 
	proof JSONB NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (episode_id), 
	FOREIGN KEY(episode_id) REFERENCES employment_episodes (id), 
	FOREIGN KEY(actor_id) REFERENCES persons (id)
)
""")
    op.execute("""
CREATE TRIGGER immutable_permanent_departures BEFORE UPDATE OR DELETE ON permanent_departures FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TRIGGER no_truncate_permanent_departures BEFORE TRUNCATE ON permanent_departures EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TABLE separation_snapshots (
	departure_id UUID NOT NULL, 
	subjects JSONB NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (departure_id), 
	FOREIGN KEY(departure_id) REFERENCES permanent_departures (id)
)
""")
    op.execute("""
CREATE TRIGGER immutable_separation_snapshots BEFORE UPDATE OR DELETE ON separation_snapshots FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TRIGGER no_truncate_separation_snapshots BEFORE TRUNCATE ON separation_snapshots EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TABLE exception_case_events (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	version INTEGER NOT NULL, 
	action VARCHAR(50) NOT NULL, 
	actor_id UUID, 
	office_id UUID, 
	facts JSONB NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT exception_revision_once UNIQUE (case_id, version), 
	FOREIGN KEY(case_id) REFERENCES academic_reconciliations (id), 
	FOREIGN KEY(actor_id) REFERENCES persons (id), 
	FOREIGN KEY(office_id) REFERENCES office_appointments (id)
)
""")
    op.execute("""
CREATE INDEX ix_exception_case_events_case_id ON exception_case_events (case_id)
""")
    op.execute("""
CREATE TRIGGER immutable_exception_case_events BEFORE UPDATE OR DELETE ON exception_case_events FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TRIGGER no_truncate_exception_case_events BEFORE TRUNCATE ON exception_case_events EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
CREATE TABLE integrity_mandates (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	reviewer_id UUID NOT NULL, 
	basis VARCHAR(500) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_until TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES academic_reconciliations (id), 
	FOREIGN KEY(reviewer_id) REFERENCES persons (id)
)
""")
    op.execute("""
CREATE TRIGGER no_truncate_integrity_mandates BEFORE TRUNCATE ON integrity_mandates EXECUTE FUNCTION reject_audit_mutation()
""")
    op.execute("""
ALTER TABLE integrity_mandates ADD CHECK (valid_from < valid_until AND length(trim(basis)) >= 3)
""")
    op.execute("""
ALTER TABLE applications DROP CONSTRAINT applications_state_check
""")
    op.execute("""
ALTER TABLE applications ADD CONSTRAINT applications_state_check CHECK (state IN ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED','WITHDRAWN','OUTCOME_RECORDED','SEPARATED','INVALIDATED'))
""")
    op.execute("""
CREATE OR REPLACE FUNCTION guard_application_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Application history is permanent'; END IF;
 IF (NEW.id,NEW.person_id,NEW.episode_id,NEW.department_id,NEW.course_id,NEW.offering_id,NEW.created_at)
 IS DISTINCT FROM (OLD.id,OLD.person_id,OLD.episode_id,OLD.department_id,OLD.course_id,OLD.offering_id,OLD.created_at)
 THEN RAISE EXCEPTION 'Application identity is immutable'; END IF;
 IF OLD.state <> 'DRAFT' AND (NEW.submitted_at,NEW.declarations) IS DISTINCT FROM (OLD.submitted_at,OLD.declarations)
 THEN RAISE EXCEPTION 'Submitted facts are immutable'; END IF;
 IF OLD.state IN ('REJECTED','WITHDRAWN','OUTCOME_RECORDED','SEPARATED','INVALIDATED') AND NOT (OLD.state='OUTCOME_RECORDED' AND NEW.state='INVALIDATED') AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)
 THEN RAISE EXCEPTION 'Terminal application cannot be reopened'; END IF;
 IF NEW.state='OUTCOME_RECORDED' AND OLD.state <> 'APPROVED' THEN RAISE EXCEPTION 'Only approved participation can conclude'; END IF;
 RETURN NEW;
END $$
""")
    op.execute("""
CREATE OR REPLACE FUNCTION validate_application_allocation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE aid uuid; a applications; n integer; s quota_allocations;
BEGIN
 aid := CASE WHEN TG_TABLE_NAME='applications' THEN (to_jsonb(NEW)->>'id')::uuid ELSE (to_jsonb(NEW)->>'application_id')::uuid END;
 SELECT * INTO a FROM applications WHERE id=aid;
 SELECT count(*) INTO n FROM application_submissions WHERE application_id=aid;
 SELECT * INTO s FROM quota_allocations WHERE application_id=aid;
 IF a.state='DRAFT' AND (n<>0 OR s.application_id IS NOT NULL) THEN RAISE EXCEPTION 'Draft must not hold quota'; END IF;
 IF a.state<>'DRAFT' AND (n<>1 OR s.application_id IS NULL) THEN RAISE EXCEPTION 'Submitted application requires snapshot and allocation'; END IF;
 IF (a.state='UNDER_REVIEW' AND s.state<>'HELD') OR (a.state='APPROVED' AND s.state<>'CONFIRMED')
 OR (a.state='OUTCOME_RECORDED' AND s.state<>'RETAINED')
 OR (a.state IN ('REJECTED','SEPARATED','INVALIDATED') AND s.state<>'RELEASED') OR (a.state='WITHDRAWN' AND s.state NOT IN ('RETAINED','RELEASED'))
 THEN RAISE EXCEPTION 'Application/allocation state mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM nptel_offerings o WHERE o.id=a.offering_id AND o.course_id<>a.course_id) THEN RAISE EXCEPTION 'Canonical course mismatch'; END IF;
 IF s.application_id IS NOT NULL AND EXISTS(SELECT 1 FROM department_topic_quotas p,application_submissions sub,primary_topic_mapping_revisions m
 WHERE p.id=s.pool_id AND sub.application_id=aid AND m.id=sub.mapping_revision_id AND (p.department_id<>a.department_id OR p.topic_id<>m.topic_id))
 THEN RAISE EXCEPTION 'Cross-topic/department movement prohibited'; END IF;
 IF a.state='OUTCOME_RECORDED' AND NOT EXISTS(SELECT 1 FROM nptel_attempts t JOIN outcome_findings f ON f.attempt_id=t.id WHERE t.person_id=a.person_id AND t.offering_id=a.offering_id AND f.outcome IN ('NO_VALID_CERT','VALID_CERT')) THEN RAISE EXCEPTION 'Conclusive independent outcome required'; END IF;
 IF a.state IN ('SEPARATED','INVALIDATED') AND NOT EXISTS (SELECT 1 FROM academic_reconciliations r JOIN exception_case_events e ON r.id=e.case_id WHERE r.application_id=aid AND ((a.state='SEPARATED' AND r.kind='SEPARATION' AND e.action IN ('Q43','Q44','Q45','Q47')) OR (a.state='INVALIDATED' AND r.kind='INTEGRITY' AND e.action='INVALIDATE'))) THEN RAISE EXCEPTION 'Closure requires recorded case decision'; END IF;
 RETURN NULL;
END $$
""")

    op.execute("""INSERT INTO exception_case_events(id, case_id, version, action, facts, recorded_at)
        SELECT gen_random_uuid(), id, 1, 'RECOVERED_CASE', context || jsonb_build_object('reason',reason), updated_at
        FROM academic_reconciliations WHERE kind='INTEGRITY'""")


def downgrade() -> None:
    raise RuntimeError("Forward-only exception case evidence")
