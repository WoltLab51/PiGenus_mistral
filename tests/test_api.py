"""
API tests for PiGenus.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from db.models import User
from security.tokens import get_password_hash
from datetime import datetime


@pytest.fixture
def setup_test_users(test_db):
    """Create test users in the database."""
    users = [
        {
            "username": "testuser",
            "password": "testpass123",
            "is_admin": False
        },
        {
            "username": "admin",
            "password": "admin123",
            "is_admin": True
        }
    ]
    
    for user_data in users:
        hashed_password = get_password_hash(user_data["password"])
        db_user = User(
            username=user_data["username"],
            hashed_password=hashed_password,
            is_admin=user_data["is_admin"]
        )
        test_db.add(db_user)
    
    test_db.commit()
    return users


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "details" in data


class TestAuthEndpoint:
    """Tests for authentication endpoints."""

    def test_get_token(self, client, setup_test_users):
        """Test getting a JWT token."""
        response = client.post(
            "/auth/token",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_get_token_invalid_credentials(self, client, setup_test_users):
        """Test getting a token with invalid credentials."""
        response = client.post(
            "/auth/token",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_get_token_nonexistent_user(self, client):
        """Test getting a token for a nonexistent user."""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        assert response.status_code == 401


class TestWorkersEndpoint:
    """Tests for worker endpoints."""

    def test_register_worker(self, client, setup_test_users, auth_headers):
        """Test registering a worker."""
        response = client.post(
            "/workers/register",
            json={
                "name": "test-worker",
                "capabilities": {"cpu_cores": 4}
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "test-worker"
        assert data["status"] == "online"

    def test_worker_heartbeat(self, client, setup_test_users, auth_headers):
        """Test worker heartbeat."""
        # First register a worker
        register_response = client.post(
            "/workers/register",
            json={
                "name": "heartbeat-worker",
                "capabilities": {}
            },
            headers=auth_headers
        )
        worker_id = register_response.json()["id"]

        # Then send heartbeat
        response = client.post(
            "/workers/heartbeat",
            json={"worker_id": worker_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == worker_id
        assert data["status"] == "online"

    def test_list_workers(self, client, setup_test_users, auth_headers):
        """Test listing workers."""
        # Register a worker first
        client.post(
            "/workers/register",
            json={
                "name": "list-worker",
                "capabilities": {}
            },
            headers=auth_headers
        )

        response = client.get(
            "/workers/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestJobsEndpoint:
    """Tests for job endpoints."""

    def test_submit_job(self, client, setup_test_users, auth_headers):
        """Test submitting a job."""
        response = client.post(
            "/jobs/submit",
            json={
                "task": {"type": "test", "data": "test"},
                "priority": 1
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert data["priority"] == 1

    def test_lease_job(self, client, setup_test_users, auth_headers):
        """Test leasing a job."""
        # First register a worker
        register_response = client.post(
            "/workers/register",
            json={
                "name": "lease-worker",
                "capabilities": {}
            },
            headers=auth_headers
        )
        worker_id = register_response.json()["id"]

        # Submit a job
        client.post(
            "/jobs/submit",
            json={
                "task": {"type": "test"},
                "priority": 1
            },
            headers=auth_headers
        )

        # Lease a job
        response = client.get(
            f"/jobs/lease?worker_id={worker_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        if data is not None:  # Job might be None if queue is empty
            assert "job" in data
            assert "lease_expires_at" in data

    def test_acknowledge_job(self, client, setup_test_users, auth_headers):
        """Test acknowledging a job."""
        # First register a worker and submit a job
        register_response = client.post(
            "/workers/register",
            json={"name": "ack-worker", "capabilities": {}},
            headers=auth_headers
        )
        worker_id = register_response.json()["id"]

        submit_response = client.post(
            "/jobs/submit",
            json={"task": {"type": "test"}, "priority": 1},
            headers=auth_headers
        )
        job_id = submit_response.json()["id"]

        # Lease the job
        lease_response = client.get(
            f"/jobs/lease?worker_id={worker_id}",
            headers=auth_headers
        )
        lease_data = lease_response.json()
        if lease_data is None:
            pytest.skip("No job available to lease")

        # Acknowledge the job
        response = client.post(
            f"/jobs/{job_id}/ack",
            json={"result": {"status": "completed"}},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"

    def test_fail_job(self, client, setup_test_users, auth_headers):
        """Test failing a job."""
        # Similar setup to acknowledge test
        register_response = client.post(
            "/workers/register",
            json={"name": "fail-worker", "capabilities": {}},
            headers=auth_headers
        )
        worker_id = register_response.json()["id"]

        submit_response = client.post(
            "/jobs/submit",
            json={"task": {"type": "test"}, "priority": 1},
            headers=auth_headers
        )
        job_id = submit_response.json()["id"]

        lease_response = client.get(
            f"/jobs/lease?worker_id={worker_id}",
            headers=auth_headers
        )
        lease_data = lease_response.json()
        if lease_data is None:
            pytest.skip("No job available to lease")

        response = client.post(
            f"/jobs/{job_id}/fail",
            json={"error": "Test error"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


class TestMemoryEndpoint:
    """Tests for memory endpoints."""

    def test_set_memory(self, client, setup_test_users, auth_headers):
        """Test setting a memory item."""
        response = client.post(
            "/memory/set",
            json={
                "key": "test_key",
                "value": {"test": "value"}
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "test_key"
        assert data["value"] == {"test": "value"}

    def test_get_memory(self, client, setup_test_users, auth_headers):
        """Test getting a memory item."""
        # First set a memory item
        client.post(
            "/memory/set",
            json={
                "key": "get_test_key",
                "value": {"get": "test"}
            },
            headers=auth_headers
        )

        # Then get it
        response = client.get(
            "/memory/get/get_test_key",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "get_test_key"
        assert data["value"] == {"get": "test"}

    def test_get_nonexistent_memory(self, client, setup_test_users, auth_headers):
        """Test getting a nonexistent memory item."""
        response = client.get(
            "/memory/get/nonexistent_key",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() is None


class TestAdminEndpoint:
    """Tests for admin endpoints."""

    def test_admin_status(self, client, setup_test_users):
        """Test admin status endpoint."""
        # Get admin token
        response = client.post(
            "/auth/token",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get(
            "/admin/status",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "workers" in data
        assert "jobs" in data
        assert "pending_jobs" in data
        assert "total_workers" in data

    def test_admin_status_unauthorized(self, client, setup_test_users, auth_headers):
        """Test that non-admin users cannot access admin endpoints."""
        response = client.get(
            "/admin/status",
            headers=auth_headers
        )
        assert response.status_code == 403
