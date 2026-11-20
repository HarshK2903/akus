"""Allow independently verified attendance pending credential issuance."""

from alembic import op

revision = "0018_exam_evidence"
down_revision = "0017_compliance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""ALTER TABLE credential_events DROP CONSTRAINT credential_events_check,
        ADD CONSTRAINT credential_events_check CHECK (kind IN ('ASSERTED','EXAM_VERIFIED','VERIFIED','REJECTED','REVOKED') AND (kind='ASSERTED')=(mandate_id IS NULL))""")


def downgrade() -> None:
    raise RuntimeError("Independent exam findings require retention.")
