"""
Pytest fixtures for PiGenus tests.
"""
import pytest
from sqlmodel import SQLModel, Session, create_engine
from db.models import *
from db.database import get_session
from fastapi.testclient import TestClient
from api.main import app
from datetime import datetime
import os

# Test database URL
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(test_db):
    """Create a test client for the FastAPI app."""
    def override_get_session():
        return test_db
    
    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "username": "testuser",
        "password": "testpass123",
        "is_admin": False
    }


@pytest.fixture
def test_admin():
    """Create a test admin user."""
    return {
        "username": "admin",
        "password": "admin123",
        "is_admin": True
    }


@pytest.fixture
def auth_token(client, test_user):
    """Get an authentication token for the test user."""
    # First create the user in the test database
    from db.models import User
    from security.tokens import get_password_hash
    
    with Session(create_engine(TEST_DATABASE_URL)) as session:
        hashed_password = get_password_hash(test_user["password"])
        db_user = User(
            username=test_user["username"],
            hashed_password=hashed_password,
            is_admin=test_user["is_admin"]
        )
        session.add(db_user)
        session.commit()
    
    # Get token
    response = client.post(
        "/auth/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_worker():
    """Create a test worker configuration."""
    return {
        "name": "test-worker",
        "capabilities": {"cpu_cores": 4, "memory_gb": 8}
    }


@pytest.fixture
def test_job():
    """Create a test job."""
    return {
        "task": {"type": "test", "data": "test data"},
        "priority": 1
    }


@pytest.fixture
def test_memory_item():
    """Create a test memory item."""
    return {
        "key": "test_key",
        "value": {"test": "value"}
    }


# Set environment variables for tests
@pytest.fixture(autouse=True)
def set_test_env():
    """Set environment variables for tests."""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["DEBUG"] = "True"
    yield
    # Clean up
    for key in ["DATABASE_URL", "SECRET_KEY", "DEBUG"]:
        if key in os.environ:
            del os.environ[key]
