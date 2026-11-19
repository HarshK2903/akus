"""Append-only draft, enrollment and independently authorized review evidence."""

from alembic import op

revision = "0011_application_workflow"
down_revision = "0010_personal_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE application_draft_revisions (
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),
      version integer NOT NULL, actor_id uuid NOT NULL REFERENCES persons(id),
      declarations jsonb NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT draft_revision_once UNIQUE(application_id,version));
    CREATE TABLE enrollment_claims (
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),
      version integer NOT NULL, actor_id uuid NOT NULL REFERENCES persons(id),
      enrolled_at timestamptz, enrolled_on date,
      source_reference varchar(500) NOT NULL, document_digest varchar(64) NOT NULL,
      observed_at timestamptz NOT NULL, reason varchar(2000) NOT NULL,
      recorded_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT enrollment_claim_version_once UNIQUE(application_id,version),
      CHECK ((enrolled_at IS NULL) <> (enrolled_on IS NULL)));
    CREATE TABLE enrollment_findings (
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),
      claim_id uuid NOT NULL REFERENCES enrollment_claims(id), version integer NOT NULL,
      outcome varchar(20) NOT NULL CHECK (outcome IN ('VERIFIED','UNRESOLVED','REJECTED')),
      actor_id uuid NOT NULL REFERENCES persons(id), office_id uuid NOT NULL REFERENCES office_appointments(id),
      enrolled_at timestamptz, enrolled_on date,
      source_reference varchar(500) NOT NULL, document_digest varchar(64) NOT NULL,
      observed_at timestamptz NOT NULL, reason varchar(2000) NOT NULL,
      recorded_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT enrollment_finding_version_once UNIQUE(application_id,version),
      CHECK ((enrolled_at IS NULL) <> (enrolled_on IS NULL)));
    CREATE TABLE withdrawal_requests (
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),
      actor_id uuid NOT NULL REFERENCES persons(id), source_reference varchar(500) NOT NULL,
      reason varchar(2000) NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE withdrawal_decisions (
      id uuid PRIMARY KEY, request_id uuid NOT NULL UNIQUE REFERENCES withdrawal_requests(id),
      actor_id uuid NOT NULL REFERENCES persons(id), office_id uuid NOT NULL REFERENCES office_appointments(id),
      decision varchar(20) NOT NULL CHECK (decision IN ('AUTHORIZE','DENY')),
      finding_id uuid REFERENCES enrollment_findings(id), facts jsonb NOT NULL,
      recorded_at timestamptz NOT NULL DEFAULT now());
    CREATE TABLE application_review_decisions (
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),
      actor_id uuid NOT NULL REFERENCES persons(id), office_id uuid NOT NULL REFERENCES office_appointments(id),
      stage varchar(20) NOT NULL, decision varchar(20) NOT NULL CHECK (decision IN ('APPROVE','REJECT')),
      facts jsonb NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now());
    """)
    tables = [
        "application_draft_revisions",
        "enrollment_claims",
        "enrollment_findings",
        "withdrawal_requests",
        "withdrawal_decisions",
        "application_review_decisions",
    ]
    for table in tables:
        if table != "withdrawal_decisions":
            op.execute(f"CREATE INDEX ix_{table}_application_id ON {table}(application_id)")
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation()"
        )
    op.execute("""
    CREATE FUNCTION check_workflow_evidence_binding() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_TABLE_NAME='enrollment_findings' THEN
      IF NOT EXISTS (
        SELECT 1 FROM enrollment_claims c WHERE c.id=NEW.claim_id AND c.application_id=NEW.application_id
      ) THEN RAISE EXCEPTION 'Enrollment evidence must belong to exact application'; END IF;
      END IF;
      IF TG_TABLE_NAME='withdrawal_decisions' THEN
      IF NEW.finding_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM enrollment_findings f JOIN withdrawal_requests r ON r.id=NEW.request_id
        WHERE f.id=NEW.finding_id AND f.application_id=r.application_id AND f.outcome='VERIFIED'
      ) THEN RAISE EXCEPTION 'Withdrawal evidence must belong to exact application'; END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER enrollment_binding BEFORE INSERT ON enrollment_findings FOR EACH ROW EXECUTE FUNCTION check_workflow_evidence_binding();
    CREATE TRIGGER withdrawal_binding BEFORE INSERT ON withdrawal_decisions FOR EACH ROW EXECUTE FUNCTION check_workflow_evidence_binding();
    """)


def downgrade() -> None:
    raise RuntimeError("Forward-only: preserve application/evidence history")
