"""Private credential dossiers, scoped designations and immutable report observations."""

from alembic import op

revision = "0017_compliance"
down_revision = "0016_archived_obligations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE credential_mandates (
        id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications,
        reviewer_id uuid NOT NULL REFERENCES persons, subject_id uuid REFERENCES canonical_subjects,
        basis varchar(500) NOT NULL, valid_from timestamptz NOT NULL, valid_until timestamptz NOT NULL,
        revoked_at timestamptz, CHECK(valid_from < valid_until AND length(trim(basis)) >= 5))""")
    op.execute("""CREATE TABLE credential_documents (
        id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications, digest varchar(64) NOT NULL UNIQUE,
        content bytea NOT NULL CHECK(octet_length(content) BETWEEN 1 AND 2097152), scan varchar(20) NOT NULL)""")
    op.execute("""CREATE TABLE credential_events (
        id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications, version integer NOT NULL,
        kind varchar(20) NOT NULL, actor_id uuid NOT NULL REFERENCES persons, mandate_id uuid REFERENCES credential_mandates,
        document_id uuid REFERENCES credential_documents, facts jsonb NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE(application_id,version), CHECK(kind IN ('ASSERTED','VERIFIED','REJECTED','REVOKED') AND (kind='ASSERTED')=(mandate_id IS NULL)))""")
    op.execute("CREATE INDEX ix_credential_as_of ON credential_events(application_id,recorded_at)")
    op.execute("""CREATE TABLE credential_identities (certificate_key varchar(220) PRIMARY KEY,
        application_id uuid NOT NULL REFERENCES applications)""")
    op.execute(
        "CREATE INDEX ix_credential_identities_application_id ON credential_identities(application_id)"
    )
    op.execute("""CREATE TABLE compliance_snapshots (id uuid PRIMARY KEY, episode_id uuid NOT NULL REFERENCES employment_episodes,
        digest varchar(64) NOT NULL, facts jsonb NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now())""")
    op.execute(
        "CREATE INDEX ix_compliance_snapshot_time ON compliance_snapshots(episode_id,recorded_at)"
    )
    for table in (
        "credential_documents",
        "credential_events",
        "credential_identities",
        "compliance_snapshots",
    ):
        op.execute(
            f"CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER immutable_table BEFORE TRUNCATE ON {table} EXECUTE FUNCTION reject_audit_mutation()"
        )
    op.execute(
        "CREATE TRIGGER audit_designation AFTER INSERT OR UPDATE ON credential_mandates FOR EACH ROW EXECUTE FUNCTION audit_case_source_order()"
    )


def downgrade() -> None:
    raise RuntimeError("Credential evidence and report observations require retention.")
