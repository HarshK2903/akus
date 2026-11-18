"""Immutable submissions, counted allocation ledger and transfer reconciliation.
Forward-only additive migration; never resets existing source data.
"""

from alembic import op

revision = "0008_admission_transfers"
down_revision = "0007_catalog_quotas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE academic_events ALTER COLUMN actor_id DROP NOT NULL")
    op.execute(
        "CREATE TABLE applications (\n\tid UUID NOT NULL, \n\tperson_id UUID NOT NULL, \n\tepisode_id UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tcourse_id UUID NOT NULL, \n\toffering_id UUID NOT NULL, \n\tstate VARCHAR(24) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tdeclarations JSONB NOT NULL, \n\tnext_office VARCHAR(20), \n\tsubmitted_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (state IN ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED','WITHDRAWN')), \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(episode_id) REFERENCES employment_episodes (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(course_id) REFERENCES nptel_courses (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(offering_id) REFERENCES nptel_offerings (id) ON DELETE RESTRICT\n)"
    )
    op.execute("CREATE INDEX ix_applications_offering_id ON applications (offering_id)")
    op.execute(
        "CREATE UNIQUE INDEX one_active_canonical_application ON applications (person_id, course_id) WHERE state IN ('UNDER_REVIEW','APPROVED')"
    )
    op.execute(
        "CREATE TABLE academic_notices (\n\tid UUID NOT NULL, \n\tapplication_id UUID NOT NULL, \n\tkind VARCHAR(60) NOT NULL, \n\tfacts JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE INDEX ix_academic_notices_application_id ON academic_notices (application_id)"
    )
    op.execute(
        "CREATE TABLE academic_reconciliations (\n\tid UUID NOT NULL, \n\tapplication_id UUID NOT NULL, \n\tkind VARCHAR(40) NOT NULL, \n\tstatus VARCHAR(16) NOT NULL, \n\treason VARCHAR(100) NOT NULL, \n\tsnapshot_id UUID, \n\tcontext JSONB NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_current_reconciliation UNIQUE (application_id, kind), \n\tCHECK (status IN ('OPEN','RESOLVED')), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE INDEX ix_academic_reconciliations_application_id ON academic_reconciliations (application_id)"
    )
    op.execute(
        "CREATE TABLE application_submissions (\n\tapplication_id UUID NOT NULL, \n\tsnapshot_id UUID NOT NULL, \n\tmapping_revision_id UUID NOT NULL, \n\toriginal_pool_id UUID NOT NULL, \n\tfacts JSONB NOT NULL, \n\tsubmitted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (application_id), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(mapping_revision_id) REFERENCES primary_topic_mapping_revisions (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(original_pool_id) REFERENCES department_topic_quotas (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE quota_allocations (\n\tapplication_id UUID NOT NULL, \n\tpool_id UUID NOT NULL, \n\tstate VARCHAR(16) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tschedule_snapshot_id UUID NOT NULL, \n\tPRIMARY KEY (application_id), \n\tCHECK (state IN ('HELD','CONFIRMED','RETAINED','RELEASED')), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(pool_id) REFERENCES department_topic_quotas (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(schedule_snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT\n)"
    )
    op.execute("CREATE INDEX ix_quota_allocations_pool_id ON quota_allocations (pool_id)")
    op.execute(
        "CREATE TABLE quota_ledger (\n\tid UUID NOT NULL, \n\tmovement_id UUID NOT NULL, \n\tapplication_id UUID NOT NULL, \n\tpool_id UUID NOT NULL, \n\tdelta INTEGER NOT NULL, \n\tkind VARCHAR(24) NOT NULL, \n\tsnapshot_id UUID NOT NULL, \n\tactor_id UUID, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (delta BETWEEN -1 AND 1), \n\tCONSTRAINT movement_pool_once UNIQUE (movement_id, pool_id), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(pool_id) REFERENCES department_topic_quotas (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT\n)"
    )
    op.execute("CREATE INDEX ix_quota_ledger_pool_id ON quota_ledger (pool_id)")
    op.execute("CREATE INDEX ix_quota_ledger_movement_id ON quota_ledger (movement_id)")
    op.execute("CREATE INDEX ix_quota_ledger_application_id ON quota_ledger (application_id)")
    op.execute(
        "CREATE TRIGGER immutable_application_submissions BEFORE UPDATE OR DELETE ON application_submissions FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_application_submissions BEFORE TRUNCATE ON application_submissions EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_quota_ledger BEFORE UPDATE OR DELETE ON quota_ledger FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_quota_ledger BEFORE TRUNCATE ON quota_ledger EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_academic_notices BEFORE UPDATE OR DELETE ON academic_notices FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_academic_notices BEFORE TRUNCATE ON academic_notices EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE FUNCTION validate_counted_pool() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE pid uuid; counted integer; balance integer; stored integer;\nBEGIN\n FOR pid IN SELECT id FROM department_topic_quotas WHERE id IN (\n CASE WHEN TG_TABLE_NAME='department_topic_quotas' THEN (to_jsonb(NEW)->>'id')::uuid ELSE (to_jsonb(NEW)->>'pool_id')::uuid END,\n CASE WHEN TG_TABLE_NAME='department_topic_quotas' THEN (to_jsonb(OLD)->>'id')::uuid ELSE (to_jsonb(OLD)->>'pool_id')::uuid END)\n LOOP\n  SELECT count(*) INTO counted FROM quota_allocations WHERE pool_id=pid AND state IN ('HELD','CONFIRMED','RETAINED');\n  SELECT coalesce(sum(delta),0) INTO balance FROM quota_ledger WHERE pool_id=pid;\n  SELECT occupied INTO stored FROM department_topic_quotas WHERE id=pid;\n  IF stored <> counted OR stored <> balance THEN RAISE EXCEPTION 'Allocation/ledger occupancy mismatch' USING ERRCODE='23514'; END IF;\n END LOOP;\n RETURN NULL;\nEND $$"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER counted_pool_integrity AFTER INSERT OR UPDATE OR DELETE ON quota_allocations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_counted_pool()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER counted_pool_integrity AFTER INSERT OR UPDATE OR DELETE ON department_topic_quotas DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_counted_pool()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER counted_pool_integrity AFTER INSERT OR UPDATE OR DELETE ON quota_ledger DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_counted_pool()"
    )
    op.execute(
        "CREATE FUNCTION guard_application_history() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Application history is permanent'; END IF;\n IF (NEW.id,NEW.person_id,NEW.episode_id,NEW.department_id,NEW.course_id,NEW.offering_id,NEW.created_at)\n IS DISTINCT FROM (OLD.id,OLD.person_id,OLD.episode_id,OLD.department_id,OLD.course_id,OLD.offering_id,OLD.created_at)\n THEN RAISE EXCEPTION 'Application identity is immutable'; END IF;\n IF OLD.state <> 'DRAFT' AND (NEW.submitted_at,NEW.declarations) IS DISTINCT FROM (OLD.submitted_at,OLD.declarations)\n THEN RAISE EXCEPTION 'Submitted facts are immutable'; END IF;\n IF OLD.state IN ('REJECTED','WITHDRAWN') AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)\n THEN RAISE EXCEPTION 'Terminal application cannot be reopened'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER application_history_guard BEFORE UPDATE OR DELETE ON applications FOR EACH ROW EXECUTE FUNCTION guard_application_history()"
    )
    op.execute(
        "CREATE FUNCTION guard_allocation_history() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Allocation history is permanent'; END IF;\n IF OLD.application_id <> NEW.application_id OR OLD.state='RELEASED' OR\n (OLD.state='RETAINED' AND NEW.pool_id <> OLD.pool_id)\n THEN RAISE EXCEPTION 'Closed allocation cannot be migrated/reopened'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER allocation_history_guard BEFORE UPDATE OR DELETE ON quota_allocations FOR EACH ROW EXECUTE FUNCTION guard_allocation_history()"
    )
    op.execute(
        "CREATE FUNCTION validate_application_allocation() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE aid uuid; a applications; n integer; s quota_allocations;\nBEGIN\n aid := CASE WHEN TG_TABLE_NAME='applications' THEN (to_jsonb(NEW)->>'id')::uuid ELSE (to_jsonb(NEW)->>'application_id')::uuid END;\n SELECT * INTO a FROM applications WHERE id=aid;\n SELECT count(*) INTO n FROM application_submissions WHERE application_id=aid;\n SELECT * INTO s FROM quota_allocations WHERE application_id=aid;\n IF a.state='DRAFT' AND (n<>0 OR s.application_id IS NOT NULL) THEN RAISE EXCEPTION 'Draft must not hold quota'; END IF;\n IF a.state<>'DRAFT' AND (n<>1 OR s.application_id IS NULL) THEN RAISE EXCEPTION 'Submitted application requires snapshot and allocation'; END IF;\n IF (a.state='UNDER_REVIEW' AND s.state<>'HELD') OR (a.state='APPROVED' AND s.state<>'CONFIRMED')\n OR (a.state='REJECTED' AND s.state<>'RELEASED') OR (a.state='WITHDRAWN' AND s.state NOT IN ('RETAINED','RELEASED'))\n THEN RAISE EXCEPTION 'Application/allocation state mismatch'; END IF;\n IF EXISTS(SELECT 1 FROM nptel_offerings o WHERE o.id=a.offering_id AND o.course_id<>a.course_id) THEN RAISE EXCEPTION 'Canonical course mismatch'; END IF;\n IF s.application_id IS NOT NULL AND EXISTS(SELECT 1 FROM department_topic_quotas p,application_submissions sub,primary_topic_mapping_revisions m\n WHERE p.id=s.pool_id AND sub.application_id=aid AND m.id=sub.mapping_revision_id AND (p.department_id<>a.department_id OR p.topic_id<>m.topic_id))\n THEN RAISE EXCEPTION 'Cross-topic/department movement prohibited'; END IF;\n RETURN NULL;\nEND $$"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER application_allocation_integrity AFTER INSERT OR UPDATE ON applications DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_application_allocation()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER application_allocation_integrity AFTER INSERT OR UPDATE ON quota_allocations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_application_allocation()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER application_allocation_integrity AFTER INSERT OR UPDATE ON application_submissions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_application_allocation()"
    )


def downgrade() -> None:
    raise RuntimeError("Forward-only application and quota history")
