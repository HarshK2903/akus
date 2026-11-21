from alembic import context

from akus import models  # noqa: F401
from akus.applications import (
    attachments,  # noqa: F401
    outcome_models,  # noqa: F401
    workflow_models,  # noqa: F401
)
from akus.applications import models as application_models  # noqa: F401
from akus.catalog import models as catalog_models  # noqa: F401
from akus.compliance import models as compliance_models  # noqa: F401
from akus.config import Settings
from akus.db import Base, database
from akus.exceptions import models as exception_models  # noqa: F401
from akus.identity import models as identity_models  # noqa: F401
from akus.people import models as people_models  # noqa: F401
from akus.quotas import models as quota_models  # noqa: F401
from akus.sources import models as source_models  # noqa: F401
from akus.workspace import models as workspace_models  # noqa: F401

engine, _ = database(Settings().database_url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
