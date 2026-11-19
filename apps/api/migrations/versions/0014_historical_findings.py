"""Preserve formal appointments and historical certificate assessments."""

from alembic import op

revision = "0014_historical_findings"
down_revision = "0013_exception_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE historical_evidence_mandates (
            id uuid PRIMARY KEY, case_id uuid NOT NULL REFERENCES academic_reconciliations(id),
            reviewer_id uuid NOT NULL REFERENCES persons(id),
            subject_id uuid REFERENCES canonical_subjects(id),
            basis varchar(500) NOT NULL, valid_from timestamptz NOT NULL, valid_until timestamptz NOT NULL,
            revoked_at timestamptz
        )
    """)
    op.execute("""
        CREATE TABLE historical_certificate_findings (
            id uuid PRIMARY KEY, application_id uuid NOT NULL UNIQUE REFERENCES applications(id),
            mandate_id uuid NOT NULL REFERENCES historical_evidence_mandates(id),
            certificate_key varchar(220) NOT NULL UNIQUE, facts jsonb NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE FUNCTION guard_case_mandate() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP <> 'UPDATE' THEN RAISE EXCEPTION 'Preserve office designation'; END IF;
            IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL OR
                (to_jsonb(OLD) - 'revoked_at') <> (to_jsonb(NEW) - 'revoked_at') THEN
                RAISE EXCEPTION 'Only a recorded mandate revocation is permitted';
            END IF;
            RETURN NEW;
        END $$;
    """)
    for table in ("integrity_mandates", "historical_evidence_mandates"):
        op.execute(
            f"CREATE TRIGGER preserve_designation BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION guard_case_mandate()"
        )
        op.execute(
            f"CREATE TRIGGER preserve_designations BEFORE TRUNCATE ON {table} EXECUTE FUNCTION reject_audit_mutation()"
        )
    op.execute(
        "CREATE TRIGGER immutable_finding BEFORE UPDATE OR DELETE ON historical_certificate_findings FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER preserve_findings BEFORE TRUNCATE ON historical_certificate_findings EXECUTE FUNCTION reject_audit_mutation()"
    )


def downgrade() -> None:
    raise RuntimeError("Historical findings and recorded mandates require preservation.")
