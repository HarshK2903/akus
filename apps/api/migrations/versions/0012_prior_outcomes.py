"""Conclusive prior outcomes, permanent no-repeat and retained completed participation.
Additive forward migration; no earlier findings, allocations or application facts rewritten.
"""

from alembic import op

revision = "0012_prior_outcomes"
down_revision = "0011_application_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "\nCREATE TABLE nptel_attempts (\n\tid UUID NOT NULL, \n\tperson_id UUID NOT NULL, \n\tcourse_id UUID NOT NULL, \n\toffering_id UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_person_run_attempt UNIQUE (person_id, offering_id), \n\tFOREIGN KEY(person_id) REFERENCES persons (id), \n\tFOREIGN KEY(course_id) REFERENCES nptel_courses (id), \n\tFOREIGN KEY(offering_id) REFERENCES nptel_offerings (id), \n\tFOREIGN KEY(department_id) REFERENCES departments (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_nptel_attempts_person_id ON nptel_attempts (person_id)")
    op.execute(
        "CREATE TRIGGER immutable_nptel_attempts BEFORE UPDATE OR DELETE ON nptel_attempts FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_nptel_attempts BEFORE TRUNCATE ON nptel_attempts EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "\nCREATE TABLE attempt_evidence (\n\tid UUID NOT NULL, \n\tattempt_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\tactor_id UUID NOT NULL, \n\tasserted_outcome VARCHAR(20) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tdocument_digest VARCHAR(64) NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT attempt_evidence_version_once UNIQUE (attempt_id, version), \n\tCHECK (asserted_outcome IN ('NO_VALID_CERT','VALID_CERT','UNRESOLVED')), \n\tFOREIGN KEY(attempt_id) REFERENCES nptel_attempts (id), \n\tFOREIGN KEY(actor_id) REFERENCES persons (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_attempt_evidence_attempt_id ON attempt_evidence (attempt_id)")
    op.execute(
        "CREATE TRIGGER immutable_attempt_evidence BEFORE UPDATE OR DELETE ON attempt_evidence FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_attempt_evidence BEFORE TRUNCATE ON attempt_evidence EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "\nCREATE TABLE outcome_findings (\n\tid UUID NOT NULL, \n\tattempt_id UUID NOT NULL, \n\tevidence_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\tactor_id UUID NOT NULL, \n\toffice_id UUID NOT NULL, \n\toutcome VARCHAR(20) NOT NULL, \n\tconcluded_on DATE, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tdocument_digest VARCHAR(64) NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT outcome_finding_version_once UNIQUE (attempt_id, version), \n\tCHECK (outcome IN ('NO_VALID_CERT','VALID_CERT','UNRESOLVED')), \n\tCHECK (outcome='UNRESOLVED' OR concluded_on IS NOT NULL), \n\tFOREIGN KEY(attempt_id) REFERENCES nptel_attempts (id), \n\tFOREIGN KEY(evidence_id) REFERENCES attempt_evidence (id), \n\tFOREIGN KEY(actor_id) REFERENCES persons (id), \n\tFOREIGN KEY(office_id) REFERENCES office_appointments (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_outcome_findings_attempt_id ON outcome_findings (attempt_id)")
    op.execute(
        "CREATE TRIGGER immutable_outcome_findings BEFORE UPDATE OR DELETE ON outcome_findings FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_outcome_findings BEFORE TRUNCATE ON outcome_findings EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute("ALTER TABLE applications DROP CONSTRAINT applications_state_check")
    op.execute(
        "ALTER TABLE applications ADD CONSTRAINT applications_state_check CHECK (state IN ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED','WITHDRAWN','OUTCOME_RECORDED'))"
    )
    op.execute(
        "CREATE OR REPLACE FUNCTION guard_application_history() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Application history is permanent'; END IF;\n IF (NEW.id,NEW.person_id,NEW.episode_id,NEW.department_id,NEW.course_id,NEW.offering_id,NEW.created_at)\n IS DISTINCT FROM (OLD.id,OLD.person_id,OLD.episode_id,OLD.department_id,OLD.course_id,OLD.offering_id,OLD.created_at)\n THEN RAISE EXCEPTION 'Application identity is immutable'; END IF;\n IF OLD.state <> 'DRAFT' AND (NEW.submitted_at,NEW.declarations) IS DISTINCT FROM (OLD.submitted_at,OLD.declarations)\n THEN RAISE EXCEPTION 'Submitted facts are immutable'; END IF;\n IF OLD.state IN ('REJECTED','WITHDRAWN','OUTCOME_RECORDED') AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)\n THEN RAISE EXCEPTION 'Terminal application cannot be reopened'; END IF;\n IF NEW.state='OUTCOME_RECORDED' AND OLD.state <> 'APPROVED' THEN RAISE EXCEPTION 'Only approved participation can conclude'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE OR REPLACE FUNCTION validate_application_allocation() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE aid uuid; a applications; n integer; s quota_allocations;\nBEGIN\n aid := CASE WHEN TG_TABLE_NAME='applications' THEN (to_jsonb(NEW)->>'id')::uuid ELSE (to_jsonb(NEW)->>'application_id')::uuid END;\n SELECT * INTO a FROM applications WHERE id=aid;\n SELECT count(*) INTO n FROM application_submissions WHERE application_id=aid;\n SELECT * INTO s FROM quota_allocations WHERE application_id=aid;\n IF a.state='DRAFT' AND (n<>0 OR s.application_id IS NOT NULL) THEN RAISE EXCEPTION 'Draft must not hold quota'; END IF;\n IF a.state<>'DRAFT' AND (n<>1 OR s.application_id IS NULL) THEN RAISE EXCEPTION 'Submitted application requires snapshot and allocation'; END IF;\n IF (a.state='UNDER_REVIEW' AND s.state<>'HELD') OR (a.state='APPROVED' AND s.state<>'CONFIRMED')\n OR (a.state='OUTCOME_RECORDED' AND s.state<>'RETAINED')\n OR (a.state='REJECTED' AND s.state<>'RELEASED') OR (a.state='WITHDRAWN' AND s.state NOT IN ('RETAINED','RELEASED'))\n THEN RAISE EXCEPTION 'Application/allocation state mismatch'; END IF;\n IF EXISTS(SELECT 1 FROM nptel_offerings o WHERE o.id=a.offering_id AND o.course_id<>a.course_id) THEN RAISE EXCEPTION 'Canonical course mismatch'; END IF;\n IF s.application_id IS NOT NULL AND EXISTS(SELECT 1 FROM department_topic_quotas p,application_submissions sub,primary_topic_mapping_revisions m\n WHERE p.id=s.pool_id AND sub.application_id=aid AND m.id=sub.mapping_revision_id AND (p.department_id<>a.department_id OR p.topic_id<>m.topic_id))\n THEN RAISE EXCEPTION 'Cross-topic/department movement prohibited'; END IF;\n IF a.state='OUTCOME_RECORDED' AND NOT EXISTS(SELECT 1 FROM nptel_attempts t JOIN outcome_findings f ON f.attempt_id=t.id WHERE t.person_id=a.person_id AND t.offering_id=a.offering_id AND f.outcome IN ('NO_VALID_CERT','VALID_CERT')) THEN RAISE EXCEPTION 'Conclusive independent outcome required'; END IF;\n RETURN NULL;\nEND $$"
    )
    op.execute(
        "CREATE FUNCTION guard_attempt_binding() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_TABLE_NAME='nptel_attempts' THEN\n  IF NOT EXISTS(SELECT 1 FROM nptel_offerings WHERE id=NEW.offering_id AND course_id=NEW.course_id) THEN RAISE EXCEPTION 'Canonical attempt binding mismatch'; END IF;\n ELSE\n  IF NOT EXISTS(SELECT 1 FROM attempt_evidence WHERE id=NEW.evidence_id AND attempt_id=NEW.attempt_id) THEN RAISE EXCEPTION 'Outcome evidence belongs to another attempt'; END IF;\n END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER attempt_binding BEFORE INSERT ON nptel_attempts FOR EACH ROW EXECUTE FUNCTION guard_attempt_binding()"
    )
    op.execute(
        "CREATE TRIGGER outcome_binding BEFORE INSERT ON outcome_findings FOR EACH ROW EXECUTE FUNCTION guard_attempt_binding()"
    )


def downgrade() -> None:
    raise RuntimeError("Forward-only permanent attempt and outcome history")
