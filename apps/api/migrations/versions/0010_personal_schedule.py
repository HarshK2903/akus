"""Person-specific scheduled exam verification; HoD authority confirmed 2026-11-18."""

from alembic import op

revision = "0010_personal_schedule"
down_revision = "0009_quota_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "\nCREATE TABLE personal_schedule_revisions (\n\tid UUID NOT NULL, \n\tapplication_id UUID NOT NULL, \n\tversion INTEGER NOT NULL, \n\tscheduled_exam_on DATE NOT NULL, \n\tsource_reference VARCHAR(500) NOT NULL, \n\tdocument_digest VARCHAR(64) NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tverified_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tactor_id UUID NOT NULL, \n\toffice_id UUID NOT NULL, \n\treason VARCHAR(2000) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_personal_schedule_version UNIQUE (application_id, version), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(actor_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(office_id) REFERENCES office_appointments (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_personal_schedule_revisions_application_id ON personal_schedule_revisions (application_id)"
    )
    op.execute(
        "\nCREATE TABLE personal_schedule_current (\n\tapplication_id UUID NOT NULL, \n\trevision_id UUID NOT NULL, \n\tPRIMARY KEY (application_id), \n\tFOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(revision_id) REFERENCES personal_schedule_revisions (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "ALTER TABLE quota_allocations ADD COLUMN personal_schedule_id UUID REFERENCES personal_schedule_revisions(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE quota_ledger ADD COLUMN personal_schedule_id UUID REFERENCES personal_schedule_revisions(id) ON DELETE RESTRICT"
    )
    op.execute(
        "CREATE TRIGGER immutable_personal_schedule BEFORE UPDATE OR DELETE ON personal_schedule_revisions FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_personal_schedule BEFORE TRUNCATE ON personal_schedule_revisions EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE TRIGGER no_truncate_personal_current BEFORE TRUNCATE ON personal_schedule_current EXECUTE FUNCTION reject_audit_mutation()"
    )
    op.execute(
        "CREATE FUNCTION guard_person_schedule_binding() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE rid uuid;\nBEGIN\n rid := CASE WHEN TG_TABLE_NAME='personal_schedule_current' THEN (to_jsonb(NEW)->>'revision_id')::uuid ELSE (to_jsonb(NEW)->>'personal_schedule_id')::uuid END;\n IF rid IS NOT NULL AND NOT EXISTS(SELECT 1 FROM personal_schedule_revisions WHERE id=rid AND application_id=NEW.application_id)\n THEN RAISE EXCEPTION 'Personal schedule belongs to a different application'; END IF;\n RETURN NEW;\nEND $$"
    )
    op.execute(
        "CREATE TRIGGER quota_allocations_personal_schedule_guard BEFORE INSERT OR UPDATE ON quota_allocations FOR EACH ROW EXECUTE FUNCTION guard_person_schedule_binding()"
    )
    op.execute(
        "CREATE TRIGGER quota_ledger_personal_schedule_guard BEFORE INSERT OR UPDATE ON quota_ledger FOR EACH ROW EXECUTE FUNCTION guard_person_schedule_binding()"
    )
    op.execute(
        "CREATE TRIGGER personal_schedule_current_personal_schedule_guard BEFORE INSERT OR UPDATE ON personal_schedule_current FOR EACH ROW EXECUTE FUNCTION guard_person_schedule_binding()"
    )
    op.execute(
        "CREATE OR REPLACE FUNCTION validate_transfer_pair() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE n integer; delta_sum integer; apps integer; sources integer; personals integer;\nBEGIN\n IF NEW.kind <> 'TRANSFER' THEN RETURN NULL; END IF;\n SELECT count(*),sum(delta),count(DISTINCT application_id),count(DISTINCT snapshot_id),count(DISTINCT coalesce(personal_schedule_id::text,'GLOBAL'))\n INTO n,delta_sum,apps,sources,personals FROM quota_ledger WHERE movement_id=NEW.movement_id AND kind='TRANSFER';\n IF n<>2 OR delta_sum<>0 OR apps<>1 OR sources<>1 OR personals<>1 OR NEW.delta=0\n THEN RAISE EXCEPTION 'Transfer requires two balanced entries for the same application and evidence' USING ERRCODE='23514'; END IF;\n RETURN NULL;\nEND $$"
    )


def downgrade() -> None:
    raise RuntimeError("Forward-only verified evidence history")
