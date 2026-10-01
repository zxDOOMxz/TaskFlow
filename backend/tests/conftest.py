import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app

# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_settings():
    # Disable external integrations during tests
    return Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key",
        supabase_enabled=False,
        web3forms_enabled=False,
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_settings] = override_get_settings


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def auth_client(client):
    # Register a user and workspace
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    })

    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
