"""Protect permanent pool identity and paired transfer history without changing data."""

from alembic import op

revision = "0009_quota_identity"
down_revision = "0008_admission_transfers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE FUNCTION guard_quota_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Quota identity and history are permanent'; END IF;
      IF (NEW.id,NEW.department_id,NEW.topic_id,NEW.academic_year_id) IS DISTINCT FROM
         (OLD.id,OLD.department_id,OLD.topic_id,OLD.academic_year_id)
      THEN RAISE EXCEPTION 'Quota key is immutable'; END IF;
      IF OLD.status='PUBLISHED' AND NEW.status<>'PUBLISHED'
      THEN RAISE EXCEPTION 'Published pool cannot be unpublished'; END IF;
      RETURN NEW;
    END $$""")
    op.execute(
        "CREATE TRIGGER quota_identity_guard BEFORE UPDATE OR DELETE ON department_topic_quotas FOR EACH ROW EXECUTE FUNCTION guard_quota_identity()"
    )
    op.execute("""CREATE FUNCTION validate_transfer_pair() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE n integer; delta_sum integer; apps integer; sources integer;
    BEGIN
      IF NEW.kind <> 'TRANSFER' THEN RETURN NULL; END IF;
      SELECT count(*),sum(delta),count(DISTINCT application_id),count(DISTINCT snapshot_id)
      INTO n,delta_sum,apps,sources FROM quota_ledger WHERE movement_id=NEW.movement_id AND kind='TRANSFER';
      IF n<>2 OR delta_sum<>0 OR apps<>1 OR sources<>1 OR NEW.delta=0
      THEN RAISE EXCEPTION 'Transfer requires two balanced entries for the same application and evidence' USING ERRCODE='23514'; END IF;
      RETURN NULL;
    END $$""")
    op.execute(
        "CREATE CONSTRAINT TRIGGER transfer_pair_integrity AFTER INSERT ON quota_ledger DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_transfer_pair()"
    )
    for table in [
        "applications",
        "quota_allocations",
        "department_topic_quotas",
        "academic_reconciliations",
    ]:
        op.execute(
            f"CREATE TRIGGER no_truncate_{table} BEFORE TRUNCATE ON {table} EXECUTE FUNCTION reject_audit_mutation()"
        )


def downgrade() -> None:
    raise RuntimeError("Forward-only quota history protection")
