"""Versioned source corrections, canonical subjects, teaching and staged imports."""

from alembic import op

revision = "0005_source_management"
down_revision = "0004_institutional_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "\nCREATE TABLE canonical_subjects (\n\tid UUID NOT NULL, \n\tcode VARCHAR(40) NOT NULL, \n\tname VARCHAR(160) NOT NULL, \n\tsource_reference VARCHAR(300) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (code)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE source_revisions (\n\tid UUID NOT NULL, \n\tentity_type VARCHAR(60) NOT NULL, \n\tentity_id UUID NOT NULL, \n\tbefore JSONB, \n\tafter JSONB NOT NULL, \n\tcontext JSONB NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_source_revisions_entity_id ON source_revisions (entity_id)")
    op.execute("CREATE INDEX ix_source_revisions_entity_type ON source_revisions (entity_type)")
    op.execute(
        "\nCREATE TABLE subject_aliases (\n\tid UUID NOT NULL, \n\tsubject_id UUID NOT NULL, \n\talias VARCHAR(160) NOT NULL, \n\tsource_reference VARCHAR(300) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT unique_subject_alias UNIQUE (alias), \n\tFOREIGN KEY(subject_id) REFERENCES canonical_subjects (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE source_imports (\n\tid UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\tkind VARCHAR(20) NOT NULL, \n\tfilename VARCHAR(150) NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tsource_reference VARCHAR(300) NOT NULL, \n\trows JSONB NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tcommitted_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tCONSTRAINT source_import_dedupe UNIQUE (kind, content_hash, source_reference), \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE teaching_assignments (\n\tid UUID NOT NULL, \n\texternal_key VARCHAR(100) NOT NULL, \n\tepisode_id UUID NOT NULL, \n\tsubject_id UUID NOT NULL, \n\tdepartment_id UUID NOT NULL, \n\tacademic_year_id UUID NOT NULL, \n\tterm VARCHAR(60) NOT NULL, \n\tstarts_on DATE NOT NULL, \n\tends_before DATE NOT NULL, \n\tsource_reference VARCHAR(300) NOT NULL, \n\tvoided BOOLEAN NOT NULL, \n\tversion INTEGER NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT teaching_interval CHECK (ends_before > starts_on), \n\tCONSTRAINT no_duplicate_teaching_interval EXCLUDE USING gist (episode_id WITH =, subject_id WITH =, department_id WITH =, daterange(starts_on, ends_before, '[)') WITH &&) WHERE (NOT voided), \n\tUNIQUE (external_key), \n\tFOREIGN KEY(episode_id) REFERENCES employment_episodes (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(subject_id) REFERENCES canonical_subjects (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(academic_year_id) REFERENCES academic_years (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_teaching_assignments_episode_id ON teaching_assignments (episode_id)"
    )
    op.execute("""
    ALTER TABLE office_appointments ADD COLUMN superseded boolean NOT NULL DEFAULT false;
    ALTER TABLE office_appointments DROP CONSTRAINT exclusive_drc_hod_globally;
    ALTER TABLE office_appointments DROP CONSTRAINT one_department_officeholder;
    ALTER TABLE office_appointments DROP CONSTRAINT no_duplicate_person_principal;
    ALTER TABLE office_appointments ADD CONSTRAINT exclusive_drc_hod_globally EXCLUDE USING gist
      (person_id WITH =, office_group WITH <>, tstzrange(valid_from,valid_until,'[)') WITH &&)
      WHERE (office_group IN ('DRC_HEAD','HOD') AND NOT superseded);
    ALTER TABLE office_appointments ADD CONSTRAINT one_department_officeholder EXCLUDE USING gist
      (department_id WITH =, office_group WITH =, tstzrange(valid_from,valid_until,'[)') WITH &&)
      WHERE (NOT superseded);
    ALTER TABLE office_appointments ADD CONSTRAINT no_duplicate_person_principal EXCLUDE USING gist
      (person_id WITH =, tstzrange(valid_from,valid_until,'[)') WITH &&)
      WHERE (office='PRINCIPAL' AND NOT superseded);
    CREATE OR REPLACE FUNCTION protect_issued_office() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Office history cannot be deleted'; END IF;
      IF TG_OP = 'INSERT' THEN
        IF NEW.original_until IS DISTINCT FROM NEW.valid_until OR NEW.superseded THEN
          RAISE EXCEPTION 'Original end must match issued end';
        END IF;
        RETURN NEW;
      END IF;
      IF (NEW.id, NEW.person_id, NEW.department_id, NEW.office, NEW.valid_from, NEW.original_until,
          NEW.source_reference, NEW.reason, NEW.recorded_at) IS DISTINCT FROM
         (OLD.id, OLD.person_id, OLD.department_id, OLD.office, OLD.valid_from, OLD.original_until,
          OLD.source_reference, OLD.reason, OLD.recorded_at) OR OLD.superseded THEN
        RAISE EXCEPTION 'Issued appointment facts are immutable';
      END IF;
      IF NEW.superseded AND NEW.valid_until IS NOT DISTINCT FROM OLD.valid_until AND NEW.version=OLD.version+1 THEN
        RETURN NEW;
      END IF;
      IF NEW.superseded OR NEW.valid_until IS NULL OR (OLD.valid_until IS NOT NULL AND NEW.valid_until >= OLD.valid_until)
         OR NEW.version <> OLD.version + 1 THEN
        RAISE EXCEPTION 'Only versioned shortening or explicit supersession is permitted';
      END IF;
      RETURN NEW;
    END; $$;
    CREATE FUNCTION record_source_revision() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE ctx jsonb;
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Source history cannot be deleted'; END IF;
      ctx := COALESCE(NULLIF(current_setting('akus.source_context', true), '')::jsonb,
        '{"reason":"Database source write; consult associated audit event or fixture provenance"}'::jsonb);
      INSERT INTO source_revisions(id,entity_type,entity_id,before,after,context)
        VALUES (gen_random_uuid(),TG_TABLE_NAME,NEW.id,
          CASE WHEN TG_OP='UPDATE' THEN to_jsonb(OLD) ELSE NULL END,to_jsonb(NEW),ctx);
      RETURN NEW;
    END; $$;
    CREATE TRIGGER immutable_source_revision BEFORE UPDATE OR DELETE ON source_revisions
      FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();
    CREATE TRIGGER immutable_source_revision_truncate BEFORE TRUNCATE ON source_revisions
      EXECUTE FUNCTION reject_audit_mutation();
    """)
    for table in (
        "persons",
        "employment_episodes",
        "faculty_department_appointments",
        "office_appointments",
        "institutional_emails",
        "administrative_grants",
        "departments",
        "academic_years",
        "canonical_subjects",
        "subject_aliases",
        "teaching_assignments",
    ):
        op.execute(f"""INSERT INTO source_revisions(id,entity_type,entity_id,before,after,context)
            SELECT gen_random_uuid(),'{table}',id,NULL,to_jsonb(t),
              '{{"reason":"Preserved pre-migration source snapshot"}}'::jsonb FROM {table} t""")
        op.execute(f"""CREATE TRIGGER source_history AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION record_source_revision()""")
        op.execute(f"""CREATE TRIGGER source_no_truncate BEFORE TRUNCATE ON {table}
            EXECUTE FUNCTION reject_audit_mutation()""")


def downgrade() -> None:
    raise RuntimeError("Forward-only migration preserves all prior source facts")
