"""
Backup service for PiGenus.
Handles database and file backups.
"""
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class BackupService:
    """Service for managing backups."""

    @staticmethod
    def get_db_path() -> str:
        """Get the database file path from settings."""
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            return db_url[10:]  # Remove 'sqlite:///'
        return ""

    @staticmethod
    def create_backup(backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of the database.
        Returns the path to the backup file, or None if failed.
        """
        db_path = BackupService.get_db_path()
        if not db_path or db_path == ":memory:":
            logger.warning("Cannot backup in-memory database")
            return None

        if not backup_dir:
            backup_dir = os.path.join(
                os.path.dirname(db_path),
                "backups"
            )

        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"pigenus_{timestamp}.db")

        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    @staticmethod
    def restore_backup(backup_path: str) -> bool:
        """
        Restore a backup to the database.
        Returns True if successful, False otherwise.
        """
        db_path = BackupService.get_db_path()
        if not db_path:
            logger.error("Cannot restore: no database path configured")
            return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(backup_path, db_path)
            logger.info(f"Backup restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    @staticmethod
    def cleanup_old_backups(days: int = 7, backup_dir: Optional[str] = None) -> int:
        """
        Clean up backups older than specified days.
        Returns the number of backups deleted.
        """
        if not backup_dir:
            db_path = BackupService.get_db_path()
            if db_path:
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            else:
                logger.error("Cannot cleanup: no backup directory")
                return 0

        if not os.path.exists(backup_dir):
            return 0

        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0

        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Removed old backup: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to remove backup {filename}: {e}")

        return deleted_count

    @staticmethod
    def list_backups(backup_dir: Optional[str] = None) -> list:
        """
        List all available backups.
        Returns a list of backup file paths.
        """
        if not backup_dir:
            db_path = BackupService.get_db_path()
            if db_path:
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            else:
                return []

        if not os.path.exists(backup_dir):
            return []

        backups = []
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                backups.append({
                    "path": filepath,
                    "filename": filename,
                    "size": os.path.getsize(filepath),
                    "modified": datetime.fromtimestamp(
                        os.path.getmtime(filepath)
                    ).isoformat()
                })

        return backups


# Singleton instance
backup_service = BackupService()
