"""Limit duplicate-office constraint to scope; do not invent cross-dept same-role policy.

Revision ID: 0003_office_scope
Revises: 0002_people_access
"""

from alembic import op

revision = "0003_office_scope"
down_revision = "0002_people_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Department/office uniqueness is already enforced separately. I02 forbids
    # DIFFERENT DRC/HOD groups across scopes, not the same role across scopes.
    op.drop_constraint("no_duplicate_person_office", "office_appointments")
    op.execute("""ALTER TABLE office_appointments
      ADD CONSTRAINT no_duplicate_person_principal EXCLUDE USING gist
      (person_id WITH =, tstzrange(valid_from, valid_until, '[)') WITH &&)
      WHERE (office='PRINCIPAL')""")


def downgrade() -> None:
    raise RuntimeError("Forward-only source-history migrations")
