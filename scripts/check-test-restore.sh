#!/usr/bin/env bash
# Rehearse a logical backup and restore using synthetic acceptance records only.
set -euo pipefail
cd "$(dirname "$0")/.."
source_db=${1:?Pass an existing isolated source ending in _test}
target_db=${2:?Pass a new target ending in _restore_test}
[[ $source_db =~ ^[a-z][a-z0-9_]*_test$ && $target_db =~ ^[a-z][a-z0-9_]*_restore_test$ && $source_db != "$target_db" ]]
psql_db() { docker compose exec -T db psql -X -v ON_ERROR_STOP=1 -U akus_demo -d "$@"; }
# CREATE refuses an existing name. No database is overwritten or removed.
docker compose exec -T db createdb -U akus_demo "$target_db"
docker compose exec -T db pg_dump -U akus_demo -Fc "$source_db" |
  docker compose exec -T db pg_restore -U akus_demo --exit-on-error --single-transaction -d "$target_db"
counts="select (select version_num from alembic_version),(select count(*) from audit_events),(select count(*) from quota_ledger),(select count(*) from credential_documents),(select count(*) from compliance_snapshots),(select count(*) from source_revisions),(select count(*) from application_attachment_revisions),(select coalesce(sum(size_bytes),0) from application_attachment_revisions where content is not null),(select md5(coalesce(string_agg(id::text || digest,'' order by id),'')) from application_attachment_revisions),(select md5(coalesce(string_agg(id::text || digest,'' order by id),'')) from credential_documents)"
source_counts=$(psql_db "$source_db" -Atc "$counts")
restore_counts=$(psql_db "$target_db" -Atc "$counts")
echo "Schema revision | audit events | quota movements | credential documents | assessment snapshots | source versions | application file revisions | application file bytes | application evidence manifest checksum | credential manifest checksum"
echo "$source_db $source_counts"
echo "$target_db $restore_counts"
[[ $source_counts == "$restore_counts" ]]
python3 scripts/check-consistency.py "$target_db"
