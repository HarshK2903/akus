"""Add institutional identity alongside preserved fictional demo sessions."""

from alembic import op

revision = "0004_institutional_identity"
down_revision = "0003_office_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "\nCREATE TABLE oidc_flows (\n\tstate_hash VARCHAR(64) NOT NULL, \n\tbrowser_hash VARCHAR(64) NOT NULL, \n\tpeer_hash VARCHAR(64) NOT NULL, \n\tnonce VARCHAR(100) NOT NULL, \n\tencrypted_verifier VARCHAR(400) NOT NULL, \n\treturn_to VARCHAR(500) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tconsumed_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (state_hash)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_oidc_flows_peer_hash ON oidc_flows (peer_hash)")
    op.execute(
        "\nCREATE TABLE account_requests (\n\tid UUID NOT NULL, \n\tissuer VARCHAR(200) NOT NULL, \n\tsubject VARCHAR(255) NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tstatus VARCHAR(30) NOT NULL, \n\tperson_id UUID, \n\treason VARCHAR(1000) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_account_request UNIQUE (issuer, subject), \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE external_identities (\n\tid UUID NOT NULL, \n\tperson_id UUID NOT NULL, \n\tissuer VARCHAR(200) NOT NULL, \n\tsubject VARCHAR(255) NOT NULL, \n\tlinked_email VARCHAR(254) NOT NULL, \n\tlinked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\trevoked_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tCONSTRAINT one_subject_identity UNIQUE (issuer, subject), \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "CREATE UNIQUE INDEX one_live_identity_per_person ON external_identities (person_id) WHERE revoked_at IS NULL"
    )
    op.execute(
        "\nCREATE TABLE institutional_emails (\n\tid UUID NOT NULL, \n\tperson_id UUID NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tnormalized_email VARCHAR(254) NOT NULL, \n\tvalid_from TIMESTAMP WITH TIME ZONE NOT NULL, \n\tvalid_until TIMESTAMP WITH TIME ZONE, \n\tsource_reference VARCHAR(300) NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT email_normalized CHECK (normalized_email=lower(email)), \n\tCONSTRAINT email_interval CHECK (valid_until IS NULL OR valid_until > valid_from), \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_institutional_email_match ON institutional_emails (normalized_email)"
    )
    op.execute("CREATE INDEX ix_institutional_emails_person_id ON institutional_emails (person_id)")
    op.execute(
        "\nCREATE TABLE institutional_sessions (\n\ttoken_hash VARCHAR(64) NOT NULL, \n\tperson_id UUID NOT NULL, \n\texternal_identity_id UUID NOT NULL, \n\tcsrf_hash VARCHAR(64) NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (token_hash), \n\tFOREIGN KEY(person_id) REFERENCES persons (id) ON DELETE RESTRICT, \n\tFOREIGN KEY(external_identity_id) REFERENCES external_identities (id) ON DELETE RESTRICT\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_institutional_sessions_person_id ON institutional_sessions (person_id)"
    )
    op.execute("""
    CREATE FUNCTION preserve_external_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Identity history cannot be deleted'; END IF;
      IF (NEW.id, NEW.person_id, NEW.issuer, NEW.subject, NEW.linked_email, NEW.linked_at)
         IS DISTINCT FROM (OLD.id, OLD.person_id, OLD.issuer, OLD.subject, OLD.linked_email, OLD.linked_at)
         OR OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL THEN
         RAISE EXCEPTION 'Identity subject links are immutable; only first revocation is permitted';
      END IF;
      RETURN NEW;
    END; $$;
    CREATE TRIGGER external_identity_history BEFORE UPDATE OR DELETE ON external_identities
      FOR EACH ROW EXECUTE FUNCTION preserve_external_identity();
    CREATE TRIGGER external_identity_no_truncate BEFORE TRUNCATE ON external_identities
      EXECUTE FUNCTION reject_audit_mutation();
    """)


def downgrade() -> None:
    raise RuntimeError("Forward-only migration preserves identity and audit history")
