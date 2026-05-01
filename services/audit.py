"""
Audit logging service for PiGenus.
"""
from sqlmodel import Session
from datetime import datetime
from db.database import engine
from db.models import AuditLog
from models.enums import AuditAction
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    def log(
        action: AuditAction,
        user_id: Optional[int] = None,
        worker_id: Optional[int] = None,
        job_id: Optional[int] = None,
        session_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an audit event.
        """
        with Session(engine) as session:
            audit_log = AuditLog(
                action=action,
                user_id=user_id,
                worker_id=worker_id,
                job_id=job_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                metadata=str(metadata) if metadata else None
            )
            session.add(audit_log)
            session.commit()
            logger.debug(f"Audit log: {action.value}")

    @staticmethod
    def get_logs(
        limit: int = 100,
        action: Optional[AuditAction] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """
        Retrieve audit logs with optional filters.
        """
        with Session(engine) as session:
            query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

            if action:
                query = query.where(AuditLog.action == action)
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if start_date:
                query = query.where(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.where(AuditLog.timestamp <= end_date)

            return session.exec(query).all()

    @staticmethod
    def cleanup_old_logs(days: int = 90) -> int:
        """
        Clean up audit logs older than specified days.
        Returns the number of logs deleted.
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        with Session(engine) as session:
            old_logs = session.exec(
                select(AuditLog).where(AuditLog.timestamp < cutoff)
            ).all()

            for log in old_logs:
                session.delete(log)

            session.commit()
            deleted_count = len(old_logs)
            logger.info(f"Cleaned up {deleted_count} old audit logs")
            return deleted_count


# Singleton instance
audit_service = AuditService()
