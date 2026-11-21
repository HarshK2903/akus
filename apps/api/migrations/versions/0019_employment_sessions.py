"""Keep a session issued for an earlier employment episode from reviving on rehire."""

from alembic import op

revision = "0019_employment_sessions"
down_revision = "0018_exam_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE source_revisions ALTER COLUMN recorded_at SET DEFAULT clock_timestamp()"
    )
    # An old token carries no episode identifier. Only attribute it where the
    # issuing day matches the person's sole known episode. Ambiguous old tokens
    # require a fresh sign-in; neither identity links nor audit rows change.
    for table, person_join, issued in (
        (
            "auth_sessions",
            "p.demo_identity_id = s.identity_id",
            "s.expires_at - interval '8 hours'",
        ),
        ("institutional_sessions", "p.id = s.person_id", "s.created_at"),
    ):
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN episode_id uuid REFERENCES employment_episodes(id)"
        )
        op.execute(f"""UPDATE {table} s SET episode_id = e.id
            FROM persons p JOIN employment_episodes e ON e.person_id = p.id
            WHERE {person_join} AND NOT EXISTS (
                SELECT 1 FROM employment_episodes other WHERE other.person_id = p.id AND other.id <> e.id)
            AND daterange(e.starts_on, e.ends_before, '[)') @> (({issued}) AT TIME ZONE 'Asia/Kolkata')::date""")


def downgrade() -> None:
    raise RuntimeError("Employment-bound sessions require retention.")
