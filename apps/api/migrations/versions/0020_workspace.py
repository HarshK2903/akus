"""Notification receipts and settings; bounded durable worker recovery."""

import sqlalchemy as sa
from alembic import op

revision = "0020_workspace"
down_revision = "0019_employment_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE notice_template_versions (id uuid PRIMARY KEY,category varchar(18) NOT NULL,version integer NOT NULL,
    heading varchar(100) NOT NULL,reason varchar(500) NOT NULL,actor_id uuid NOT NULL REFERENCES persons(id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),CONSTRAINT one_notice_template_version UNIQUE(category,version))""")
    op.execute("""CREATE TABLE personal_test_notices(id uuid PRIMARY KEY,person_id uuid NOT NULL REFERENCES persons(id),
    category varchar(18) NOT NULL,heading varchar(100) NOT NULL,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    op.create_index("ix_personal_test_notices_person_id", "personal_test_notices", ["person_id"])
    op.execute("""CREATE TABLE personal_notice_reads(person_id uuid NOT NULL REFERENCES persons(id),notice_id uuid NOT NULL,
    read_at timestamptz NOT NULL DEFAULT clock_timestamp(),PRIMARY KEY(person_id,notice_id))""")
    op.execute("""CREATE TABLE personal_notice_preferences(person_id uuid PRIMARY KEY REFERENCES persons(id),initial_filter varchar(10) NOT NULL
    CHECK(initial_filter IN ('ALL','UNREAD')))""")
    for table in ("notice_template_versions", "personal_test_notices", "personal_notice_reads"):
        op.execute(
            f"CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER immutable_table BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation()"
        )
    op.add_column(
        "work_jobs", sa.Column("attempts", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("work_jobs", sa.Column("last_error", sa.String(90)))
    op.add_column("work_jobs", sa.Column("next_attempt_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    raise RuntimeError("Notification and operations history requires retention.")
