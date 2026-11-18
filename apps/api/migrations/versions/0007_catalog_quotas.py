"""Canonical catalog, provider observations, HoD mappings and annual shared quotas.

Forward-only; preserves all existing source and identity data.
"""

from alembic import op

revision = "0007_catalog_quotas"
down_revision = "0006_identity_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE nptel_courses (\n\tid UUID NOT NULL, \n\tcode VARCHAR(80) NOT NULL, \n\ttitle VARCHAR(240) NOT NULL, \n\tdescription VARCHAR(12000) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (code)\n)"
    )
    op.execute(
        "CREATE TABLE nptel_topics (\n\tid UUID NOT NULL, \n\tcode VARCHAR(40) NOT NULL, \n\tname VARCHAR(160) NOT NULL, \n\tnormalized_name VARCHAR(160) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (code), \n\tUNIQUE (normalized_name)\n)"
    )
    op.execute(
        "CREATE TABLE department_course_mappings (\n\tid UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tcourse_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_department_course_mapping UNIQUE (department_id, course_id), \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(course_id) REFERENCES nptel_courses (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE department_topic_quotas (\n\tid UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\ttopic_id UUID NOT NULL, \n\tacademic_year_id UUID NOT NULL, \n\tmaximum INTEGER NOT NULL, \n\toccupied INTEGER NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tpublished_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_annual_shared_topic_pool UNIQUE (department_id, topic_id, academic_year_id), \n\tCONSTRAINT quota_capacity_bounds CHECK (maximum >= 0 AND occupied >= 0 AND occupied <= maximum), \n\tCHECK (status IN ('DRAFT','PUBLISHED')), \n\tCHECK (status <> 'DRAFT' OR occupied = 0), \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(topic_id) REFERENCES nptel_topics (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(academic_year_id) REFERENCES academic_years (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE nptel_offerings (\n\tid UUID NOT NULL, \n\tcourse_id UUID NOT NULL, \n\tprovider_id VARCHAR(80) NOT NULL, \n\tcurrent_snapshot_id UUID, \n\tversion INTEGER NOT NULL, \n\tsource_status VARCHAR(40) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(course_id) REFERENCES nptel_courses (id) ON DELETE RESTRICT, \n\tUNIQUE (provider_id)\n)"
    )
    op.execute("CREATE INDEX ix_nptel_offerings_course_id ON nptel_offerings (course_id)")
    op.execute(
        "CREATE TABLE nptel_topic_aliases (\n\tid UUID NOT NULL, \n\tlabel VARCHAR(160) NOT NULL, \n\tnormalized_label VARCHAR(160) NOT NULL, \n\ttopic_id UUID NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (normalized_label), \n\tFOREIGN KEY(topic_id) REFERENCES nptel_topics (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE academic_events (\n\tid UUID NOT NULL, \n\tentity_id UUID NOT NULL, \n\tkind VARCHAR(60) NOT NULL, \n\tactor_id UUID NOT NULL, \n\tdepartment_id UUID, \n\tdata JSONB NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT\n)"
    )
    op.execute("CREATE INDEX ix_academic_events_entity_id ON academic_events (entity_id)")
    op.execute(
        "CREATE TABLE nptel_topic_proposals (\n\tid UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tperson_id UUID NOT NULL, \n\tnormalized_label VARCHAR(160) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\ttopic_id UUID, \n\tstatus VARCHAR(30) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT deduplicate_topic_proposal UNIQUE (department_id, normalized_label), \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(topic_id) REFERENCES nptel_topics (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE provider_snapshots (\n\tid UUID NOT NULL, \n\toffering_id UUID NOT NULL, \n\tdigest VARCHAR(64) NOT NULL, \n\tsource_url VARCHAR(500) NOT NULL, \n\ttrust VARCHAR(30) NOT NULL, \n\tparser_version VARCHAR(40) NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tmetadata_json JSONB NOT NULL, \n\tactor_id UUID NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (trust IN ('OFFICIAL_HTTPS','LOCAL_DEMO')), \n\tFOREIGN KEY(offering_id) REFERENCES nptel_offerings (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT\n)"
    )
    op.execute("CREATE INDEX ix_provider_snapshots_offering_id ON provider_snapshots (offering_id)")
    op.execute(
        "CREATE TABLE primary_topic_mapping_requests (\n\tid UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tcourse_id UUID NOT NULL, \n\tsnapshot_id UUID NOT NULL, \n\trequested_by UUID NOT NULL, \n\tstatus VARCHAR(30) NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT deduplicate_mapping_request UNIQUE (department_id, course_id, snapshot_id), \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(course_id) REFERENCES nptel_courses (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(requested_by) REFERENCES persons (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE primary_topic_mapping_revisions (\n\tid UUID NOT NULL, \n\tmapping_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\ttopic_id UUID NOT NULL, \n\tsnapshot_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\toffice_id UUID NOT NULL, \n\tvalid_from TIMESTAMP WITH TIME ZONE NOT NULL, \n\tvalid_until TIMESTAMP WITH TIME ZONE, \n\treason VARCHAR(2000) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tpolicy VARCHAR(80) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT mapping_revision_unique UNIQUE (mapping_id, version), \n\tCHECK (valid_until IS NULL OR valid_until > valid_from), \n\tCONSTRAINT nonoverlapping_primary_mapping EXCLUDE USING gist (mapping_id WITH =, tstzrange(valid_from, valid_until, '[)') WITH &&), \n\tFOREIGN KEY(mapping_id) REFERENCES department_course_mappings (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(topic_id) REFERENCES nptel_topics (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(office_id) REFERENCES office_appointments (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE UNIQUE INDEX one_current_primary_topic ON primary_topic_mapping_revisions (mapping_id) WHERE valid_until IS NULL"
    )
    op.execute(
        "CREATE TABLE provider_fetches (\n\tid UUID NOT NULL, \n\toffering_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tstatus VARCHAR(40) NOT NULL, \n\terror_code VARCHAR(60), \n\tsnapshot_id UUID, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(offering_id) REFERENCES nptel_offerings (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "CREATE TABLE topic_quota_revisions (\n\tid UUID NOT NULL, \n\tpool_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\tprevious_maximum INTEGER, \n\tmaximum INTEGER NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tactor_id UUID NOT NULL, \n\toffice_id UUID NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT quota_revision_unique UNIQUE (pool_id, version), \n\tFOREIGN KEY(pool_id) REFERENCES department_topic_quotas (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(office_id) REFERENCES office_appointments (id) ON DELETE RESTRICT\n)"
    )
    op.execute(
        "ALTER TABLE nptel_offerings ADD CONSTRAINT offering_current_snapshot_fk FOREIGN KEY(current_snapshot_id) REFERENCES provider_snapshots (id) ON DELETE RESTRICT"
    )
    op.execute(
        "CREATE TRIGGER immutable_provider_snapshots BEFORE UPDATE OR DELETE ON provider_snapshots FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_provider_snapshots BEFORE TRUNCATE ON provider_snapshots EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_provider_fetches BEFORE UPDATE OR DELETE ON provider_fetches FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_provider_fetches BEFORE TRUNCATE ON provider_fetches EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_academic_events BEFORE UPDATE OR DELETE ON academic_events FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_academic_events BEFORE TRUNCATE ON academic_events EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_topic_quota_revisions BEFORE UPDATE OR DELETE ON topic_quota_revisions FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_topic_quota_revisions BEFORE TRUNCATE ON topic_quota_revisions EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER immutable_nptel_topic_aliases BEFORE UPDATE OR DELETE ON nptel_topic_aliases FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_nptel_topic_aliases BEFORE TRUNCATE ON nptel_topic_aliases EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE FUNCTION guard_mapping_history() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_OP <> 'UPDATE' THEN RAISE EXCEPTION 'Mapping history is immutable'; END IF;\n IF OLD.valid_until IS NOT NULL OR NEW.valid_until IS NULL OR NEW.valid_until <= OLD.valid_from\n OR (to_jsonb(NEW) - 'valid_until') IS DISTINCT FROM (to_jsonb(OLD) - 'valid_until')\n THEN RAISE EXCEPTION 'Only closing a current mapping revision is permitted'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER mapping_history_guard BEFORE UPDATE OR DELETE ON primary_topic_mapping_revisions FOR EACH ROW EXECUTE FUNCTION guard_mapping_history()"
    )
    op.execute(
        "CREATE TRIGGER mapping_history_no_truncate BEFORE TRUNCATE ON primary_topic_mapping_revisions EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE FUNCTION guard_offering_identity() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Offering identity is permanent'; END IF;\n IF (NEW.id, NEW.course_id, NEW.provider_id) IS DISTINCT FROM (OLD.id, OLD.course_id, OLD.provider_id)\n THEN RAISE EXCEPTION 'Offering identity is permanent'; END IF;\n IF NEW.current_snapshot_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM provider_snapshots WHERE id=NEW.current_snapshot_id AND offering_id=NEW.id)\n THEN RAISE EXCEPTION 'Snapshot does not belong to offering'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER offering_identity_guard BEFORE UPDATE OR DELETE ON nptel_offerings FOR EACH ROW EXECUTE FUNCTION guard_offering_identity()"
    )


def downgrade() -> None:
    raise RuntimeError("Forward-only catalog and academic history migration")
