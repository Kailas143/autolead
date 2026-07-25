import os
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

# Ensure tests use an in-memory SQLite database instead of the default Postgres URL.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import models
from app.api import deps
from app.core import database
from app.main import app

# Replace the backend database engine with an in-memory SQLite engine for tests.
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
database.engine = test_engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Ensure the FastAPI app uses the same test engine during startup.
import app.main as app_main
app_main.engine = test_engine

# Create the schema once for the test session.
database.Base.metadata.create_all(bind=test_engine)

SessionTesting = database.SessionLocal

@pytest.fixture(scope="function")
def db():
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_user(db):
    user = models.User(
        email=f"test+{uuid.uuid4().hex}@example.com",
        hashed_password="fake",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def client(db, test_user):
    def override_get_db():
        session = SessionTesting()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: test_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
