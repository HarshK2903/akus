"""Preserve provider-verified email observations and full academic-year provenance."""

import sqlalchemy as sa
from alembic import op

revision = "0006_identity_history"
down_revision = "0005_source_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institutional_sessions",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column("academic_years", "source", type_=sa.String(300), existing_type=sa.String(50))
    op.create_table(
        "verified_email_observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "external_identity_id",
            sa.Uuid(),
            sa.ForeignKey("external_identities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "external_identity_id", "email", name="verified_email_observation_once"
        ),
    )
    op.execute("""INSERT INTO verified_email_observations(id,external_identity_id,email,observed_at)
        SELECT gen_random_uuid(),id,linked_email,linked_at FROM external_identities""")
    op.execute("""CREATE TRIGGER immutable_verified_email BEFORE UPDATE OR DELETE ON verified_email_observations
        FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();
        CREATE TRIGGER immutable_verified_email_truncate BEFORE TRUNCATE ON verified_email_observations
        EXECUTE FUNCTION reject_audit_mutation();""")


def downgrade() -> None:
    raise RuntimeError("Forward-only identity/source history migration")
