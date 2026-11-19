"""Distinguish an existing formally adjudicated obligation from raw teaching data."""

from alembic import op

revision = "0016_archived_obligations"
down_revision = "0015_designation_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE archived_subject_obligations (
            id UUID PRIMARY KEY, episode_id UUID NOT NULL REFERENCES employment_episodes(id),
            subject_id UUID NOT NULL REFERENCES canonical_subjects(id), first_assignment DATE NOT NULL,
            decided_on DATE NOT NULL, decision_reference VARCHAR(500) NOT NULL,
            authority_basis VARCHAR(500) NOT NULL, document_digest VARCHAR(64) NOT NULL,
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT one_archived_obligation UNIQUE(episode_id, subject_id),
            CHECK(document_digest ~ '^[0-9a-f]{64}$' AND length(trim(authority_basis)) >= 5 AND length(trim(decision_reference)) >= 3)
        )
    """)
    op.execute(
        "CREATE TRIGGER preserve_archived_obligation BEFORE UPDATE OR DELETE ON archived_subject_obligations FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER preserve_archived_obligations BEFORE TRUNCATE ON archived_subject_obligations EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute("""
        CREATE FUNCTION audit_case_source_order() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            INSERT INTO audit_events(id,action,recorded_at,details) VALUES
                (gen_random_uuid(),'CASE_SOURCE_ORDER',clock_timestamp(),
                 jsonb_build_object('table',TG_TABLE_NAME,'operation',TG_OP,'id',NEW.id,
                                    'database_principal',session_user,'facts',to_jsonb(NEW)));
            RETURN NEW;
        END $$;
    """)
    for table in (
        "integrity_mandates",
        "historical_evidence_mandates",
        "archived_subject_obligations",
    ):
        op.execute(
            f"CREATE TRIGGER audit_source_order AFTER INSERT OR UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION audit_case_source_order()"
        )


def downgrade() -> None:
    raise RuntimeError("Preserve archival source orders and their audit evidence.")
