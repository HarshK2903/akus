import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from akus.config import Settings
from akus.main import create_app
from akus.seed import seed


@pytest.fixture(scope="session")
def settings() -> Settings:
    url = os.environ.get(
        "AKUS_TEST_DATABASE_URL",
        "postgresql+psycopg://akus_demo:akus_demo@127.0.0.1:55432/akus_test",
    )
    if not url.rsplit("/", 1)[-1].endswith("_test"):
        raise RuntimeError("Tests require an explicitly separate _test database")
    return Settings(env="test", demo_enabled=True, database_url=url, _env_file=None)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with app.state.sessions() as db:
        seed(db)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


@pytest.fixture
def db(client: TestClient) -> Iterator[Session]:
    with client.app.state.sessions() as session:  # type: ignore[union-attr]
        yield session
