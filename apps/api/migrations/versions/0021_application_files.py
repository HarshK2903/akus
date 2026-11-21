"""Private, immutable application attachment revisions with preserved draft removals."""

from alembic import op

revision = "0021_application_files"
down_revision = "0020_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE application_attachment_revisions(
      id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES applications(id),series_id uuid NOT NULL,
      version integer NOT NULL,actor_id uuid NOT NULL REFERENCES persons(id),kind varchar(24) NOT NULL,filename varchar(140) NOT NULL,
      source_reference varchar(500) NOT NULL,reason varchar(2000) NOT NULL,digest varchar(64) NOT NULL,
      size_bytes integer NOT NULL,scan varchar(20) NOT NULL,content bytea,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      CONSTRAINT one_application_attachment_revision UNIQUE(application_id,series_id,version),
      CONSTRAINT valid_application_attachment CHECK(version>=1 AND size_bytes BETWEEN 1 AND 2097152 AND
      ((scan IN ('CLEAN','QUARANTINED') AND content IS NOT NULL AND octet_length(content)=size_bytes AND encode(sha256(content),'hex')=digest) OR (scan='REMOVED' AND content IS NULL))))""")
    op.execute(
        "CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON application_attachment_revisions FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_table BEFORE TRUNCATE ON application_attachment_revisions FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation()"
    )


def downgrade() -> None:
    raise RuntimeError("Application evidence history requires retention.")
