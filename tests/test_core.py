"""
Core logic tests for PiGenus.
"""
import pytest
from datetime import datetime, timedelta
from core.config import Settings, settings
from core.scheduler import (
    rotate_logs,
    backup_database,
    requeue_stuck_jobs,
    nightly_jobs
)
from services.audit import audit_service, AuditService
from services.backup import backup_service, BackupService
from models.enums import AuditAction
from db.models import AuditLog, Job, JobStatus
from sqlmodel import Session, create_engine, select
import os
import time


class TestConfig:
    """Tests for configuration."""

    def test_settings_from_env(self, monkeypatch):
        """Test that settings are loaded from environment variables."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("DEBUG", "True")
        
        # Reload settings
        from importlib import reload
        import core.config
        reload(core.config)
        from core.config import settings
        
        assert settings.secret_key == "test-secret"
        assert settings.database_url == "sqlite:///test.db"
        assert settings.debug is True

    def test_default_settings(self):
        """Test default settings values."""
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.worker_lease_timeout == 60


class TestScheduler:
    """Tests for scheduler functions."""

    def test_rotate_logs(self, tmp_path, monkeypatch):
        """Test log rotation."""
        # Create a test log file
        log_file = tmp_path / "pigenus.log"
        log_file.write_text("Test log content\n")
        
        # Change to tmp_path
        monkeypatch.chdir(tmp_path)
        
        # Run rotation
        rotate_logs()
        
        # Check that log was rotated
        assert not log_file.exists()
        assert (tmp_path / "pigenus.log.1").exists()

    def test_backup_database(self, tmp_path, monkeypatch):
        """Test database backup."""
        # Create a test database
        db_path = tmp_path / "test.db"
        db_path.touch()
        
        # Mock the database URL
        monkeypatch.setattr(
            "core.scheduler.settings",
            Settings(database_url=f"sqlite:///{db_path}")
        )
        
        # Create backups directory
        backups_dir = tmp_path / "backups"
        backups_dir.mkdir()
        
        # Run backup
        backup_database()
        
        # Check that backup was created
        backup_files = list(backups_dir.glob("pigenus_*.db"))
        assert len(backup_files) == 1

    def test_requeue_stuck_jobs(self, test_db):
        """Test requeuing stuck jobs."""
        # Create a stuck job (leased long ago)
        old_lease_time = datetime.utcnow() - timedelta(minutes=10)
        stuck_job = Job(
            task='{"type": "test"}',
            status=JobStatus.LEASED,
            priority=1,
            created_at=datetime.utcnow(),
            leased_at=old_lease_time,
            worker_id=1
        )
        test_db.add(stuck_job)
        test_db.commit()

        # Mock the lease timeout
        import core.scheduler
        original_timeout = core.scheduler.settings.worker_lease_timeout
        core.scheduler.settings.worker_lease_timeout = 60  # 60 seconds

        try:
            # Run requeue
            requeue_stuck_jobs()

            # Check that job was requeued
            requeued_job = test_db.exec(
                select(Job).where(Job.id == stuck_job.id)
            ).first()
            assert requeued_job.status == JobStatus.PENDING
            assert requeued_job.leased_at is None
            assert requeued_job.worker_id is None
        finally:
            core.scheduler.settings.worker_lease_timeout = original_timeout


class TestAuditService:
    """Tests for audit service."""

    def test_log_action(self, test_db):
        """Test logging an audit action."""
        audit_service.log(
            action=AuditAction.JOB_SUBMITTED,
            user_id=1,
            job_id=1,
            metadata={"test": "data"}
        )

        # Check that log was created
        logs = test_db.exec(select(AuditLog)).all()
        assert len(logs) == 1
        assert logs[0].action == AuditAction.JOB_SUBMITTED
        assert logs[0].user_id == 1
        assert logs[0].job_id == 1

    def test_get_logs(self, test_db):
        """Test retrieving audit logs."""
        # Add some logs
        audit_service.log(action=AuditAction.JOB_SUBMITTED, user_id=1)
        audit_service.log(action=AuditAction.WORKER_REGISTERED, user_id=2)

        # Get logs
        logs = audit_service.get_logs(limit=10)
        assert len(logs) == 2

    def test_cleanup_old_logs(self, test_db):
        """Test cleaning up old logs."""
        # Add an old log
        old_log = AuditLog(
            action=AuditAction.JOB_SUBMITTED,
            timestamp=datetime.utcnow() - timedelta(days=100),
            metadata="{}"
        )
        test_db.add(old_log)
        test_db.commit()

        # Cleanup
        deleted_count = audit_service.cleanup_old_logs(days=90)
        assert deleted_count == 1

        # Check that log was deleted
        logs = test_db.exec(select(AuditLog)).all()
        assert len(logs) == 0


class TestBackupService:
    """Tests for backup service."""

    def test_get_db_path(self, monkeypatch):
        """Test getting database path."""
        monkeypatch.setattr(
            "services.backup.settings",
            Settings(database_url="sqlite:///test.db")
        )
        assert backup_service.get_db_path() == "test.db"

    def test_create_backup(self, tmp_path, monkeypatch):
        """Test creating a backup."""
        # Create a test database
        db_path = tmp_path / "test.db"
        db_path.touch()
        
        monkeypatch.setattr(
            "services.backup.settings",
            Settings(database_url=f"sqlite:///{db_path}")
        )
        
        # Create backup
        backup_path = backup_service.create_backup(backup_dir=str(tmp_path))
        
        assert backup_path is not None
        assert (tmp_path / os.path.basename(backup_path)).exists()

    def test_list_backups(self, tmp_path, monkeypatch):
        """Test listing backups."""
        # Create some backup files
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        (backup_dir / "pigenus_20260101_120000.db").touch()
        (backup_dir / "pigenus_20260102_120000.db").touch()
        
        monkeypatch.setattr(
            "services.backup.settings",
            Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
        )
        
        # List backups
        backups = backup_service.list_backups(backup_dir=str(backup_dir))
        
        assert len(backups) == 2
        assert all("pigenus_" in b["filename"] for b in backups)

    def test_cleanup_old_backups(self, tmp_path, monkeypatch):
        """Test cleaning up old backups."""
        # Create old and new backup files
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        # Old backup (10 days old)
        old_backup = backup_dir / "pigenus_old.db"
        old_backup.touch()
        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_backup, (old_time, old_time))
        
        # New backup (1 day old)
        new_backup = backup_dir / "pigenus_new.db"
        new_backup.touch()
        new_time = time.time() - (1 * 24 * 60 * 60)
        os.utime(new_backup, (new_time, new_time))
        
        monkeypatch.setattr(
            "services.backup.settings",
            Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
        )
        
        # Cleanup
        deleted_count = backup_service.cleanup_old_backups(
            days=5,
            backup_dir=str(backup_dir)
        )
        
        assert deleted_count == 1
        assert not old_backup.exists()
        assert new_backup.exists()
