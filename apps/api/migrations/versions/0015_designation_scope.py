"""Separate the authority to verify a negative roster from certificate authentication."""

from alembic import op

revision = "0015_designation_scope"
down_revision = "0014_historical_findings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE historical_evidence_mandates
        ADD COLUMN purpose varchar(24) NOT NULL DEFAULT 'CERTIFICATE',
        ADD CHECK (purpose IN ('CERTIFICATE','ENROLLMENT_ABSENCE')),
        ADD CHECK (valid_from < valid_until AND length(trim(basis)) >= 3)
    """)


def downgrade() -> None:
    raise RuntimeError("Designation history must be preserved.")
