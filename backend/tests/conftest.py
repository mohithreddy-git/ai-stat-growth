import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-for-phase-one-validation-26101"
os.environ["CORS_ORIGINS"] = "http://testserver"

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.seed import seed_database  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(seeded_database):
    with TestClient(app) as test_client:
        yield test_client
