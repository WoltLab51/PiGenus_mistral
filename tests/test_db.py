"""
Database tests for PiGenus.
"""
import pytest
from sqlmodel import Session, create_engine, select
from db.models import *
from db.database import get_session, init_db
from datetime import datetime
from models.enums import JobStatus, WorkerStatus, AuditAction


class TestDatabaseModels:
    """Tests for database models."""

    def test_create_user(self, test_db):
        """Test creating a user."""
        user = User(
            username="testuser",
            hashed_password="hashed_password",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()

        # Check user was created
        db_user = test_db.exec(
            select(User).where(User.username == "testuser")
        ).first()
        assert db_user is not None
        assert db_user.username == "testuser"
        assert db_user.is_admin is False

    def test_create_worker(self, test_db):
        """Test creating a worker."""
        # First create a user
        user = User(
            username="worker_owner",
            hashed_password="password",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()

        # Then create a worker
        worker = Worker(
            name="test-worker",
            capabilities='{"cpu_cores": 4}',
            status=WorkerStatus.ONLINE,
            last_heartbeat=datetime.utcnow(),
            owner_id=user.id
        )
        test_db.add(worker)
        test_db.commit()

        # Check worker was created
        db_worker = test_db.exec(
            select(Worker).where(Worker.name == "test-worker")
        ).first()
        assert db_worker is not None
        assert db_worker.name == "test-worker"
        assert db_worker.status == WorkerStatus.ONLINE

    def test_create_job(self, test_db):
        """Test creating a job."""
        job = Job(
            task='{"type": "test", "data": "test"}',
            status=JobStatus.PENDING,
            priority=1,
            created_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()

        # Check job was created
        db_job = test_db.exec(
            select(Job).where(Job.id == job.id)
        ).first()
        assert db_job is not None
        assert db_job.status == JobStatus.PENDING
        assert db_job.priority == 1

    def test_create_session(self, test_db):
        """Test creating a session."""
        # First create a user
        user = User(
            username="session_user",
            hashed_password="password",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()

        # Then create a session
        session = DbSession(
            user_id=user.id,
            created_at=datetime.utcnow()
        )
        test_db.add(session)
        test_db.commit()

        # Check session was created
        db_session = test_db.exec(
            select(DbSession).where(DbSession.id == session.id)
        ).first()
        assert db_session is not None
        assert db_session.user_id == user.id

    def test_create_audit_log(self, test_db):
        """Test creating an audit log."""
        audit_log = AuditLog(
            action=AuditAction.JOB_SUBMITTED,
            user_id=1,
            job_id=1,
            timestamp=datetime.utcnow(),
            metadata='{"test": "data"}'
        )
        test_db.add(audit_log)
        test_db.commit()

        # Check audit log was created
        db_log = test_db.exec(
            select(AuditLog).where(AuditLog.id == audit_log.id)
        ).first()
        assert db_log is not None
        assert db_log.action == AuditAction.JOB_SUBMITTED


class TestDatabaseRelationships:
    """Tests for database relationships."""

    def test_user_workers_relationship(self, test_db):
        """Test user to workers relationship."""
        # Create a user
        user = User(
            username="relationship_user",
            hashed_password="password",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()

        # Create workers for the user
        worker1 = Worker(
            name="worker1",
            capabilities="{}",
            status=WorkerStatus.ONLINE,
            last_heartbeat=datetime.utcnow(),
            owner_id=user.id
        )
        worker2 = Worker(
            name="worker2",
            capabilities="{}",
            status=WorkerStatus.OFFLINE,
            last_heartbeat=datetime.utcnow(),
            owner_id=user.id
        )
        test_db.add(worker1)
        test_db.add(worker2)
        test_db.commit()

        # Check relationship
        db_user = test_db.exec(
            select(User).where(User.id == user.id)
        ).first()
        assert len(db_user.workers) == 2

    def test_worker_jobs_relationship(self, test_db):
        """Test worker to jobs relationship."""
        # Create a user and worker
        user = User(
            username="job_user",
            hashed_password="password",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()

        worker = Worker(
            name="job_worker",
            capabilities="{}",
            status=WorkerStatus.ONLINE,
            last_heartbeat=datetime.utcnow(),
            owner_id=user.id
        )
        test_db.add(worker)
        test_db.commit()

        # Create jobs for the worker
        job1 = Job(
            task='{"type": "test1"}',
            status=JobStatus.COMPLETED,
            priority=1,
            created_at=datetime.utcnow(),
            worker_id=worker.id
        )
        job2 = Job(
            task='{"type": "test2"}',
            status=JobStatus.PENDING,
            priority=2,
            created_at=datetime.utcnow(),
            worker_id=worker.id
        )
        test_db.add(job1)
        test_db.add(job2)
        test_db.commit()

        # Check relationship
        db_worker = test_db.exec(
            select(Worker).where(Worker.id == worker.id)
        ).first()
        assert len(db_worker.jobs) == 2


class TestDatabaseQueries:
    """Tests for complex database queries."""

    def test_query_jobs_by_status(self, test_db):
        """Test querying jobs by status."""
        # Create jobs with different statuses
        jobs = [
            Job(
                task='{"type": "test1"}',
                status=JobStatus.PENDING,
                priority=1,
                created_at=datetime.utcnow()
            ),
            Job(
                task='{"type": "test2"}',
                status=JobStatus.LEASED,
                priority=2,
                created_at=datetime.utcnow()
            ),
            Job(
                task='{"type": "test3"}',
                status=JobStatus.COMPLETED,
                priority=3,
                created_at=datetime.utcnow()
            )
        ]
        for job in jobs:
            test_db.add(job)
        test_db.commit()

        # Query pending jobs
        pending_jobs = test_db.exec(
            select(Job).where(Job.status == JobStatus.PENDING)
        ).all()
        assert len(pending_jobs) == 1

    def test_query_jobs_by_priority(self, test_db):
        """Test querying jobs by priority."""
        # Create jobs with different priorities
        jobs = [
            Job(
                task='{"type": "low"}',
                status=JobStatus.PENDING,
                priority=1,
                created_at=datetime.utcnow()
            ),
            Job(
                task='{"type": "medium"}',
                status=JobStatus.PENDING,
                priority=5,
                created_at=datetime.utcnow()
            ),
            Job(
                task='{"type": "high"}',
                status=JobStatus.PENDING,
                priority=10,
                created_at=datetime.utcnow()
            )
        ]
        for job in jobs:
            test_db.add(job)
        test_db.commit()

        # Query by priority (highest first)
        high_priority_jobs = test_db.exec(
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .order_by(Job.priority.desc())
        ).all()
        
        assert high_priority_jobs[0].priority == 10
        assert high_priority_jobs[1].priority == 5
        assert high_priority_jobs[2].priority == 1
