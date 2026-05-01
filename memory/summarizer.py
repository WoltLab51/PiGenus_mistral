"""
Session summarization service for PiGenus.
Creates summaries of sessions for long-term memory.
"""
from sqlmodel import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from db.database import engine
from db.models import Session as DbSession, Message, Job, MemoryItem
from services.audit import audit_service
from models.enums import AuditAction
import logging

logger = logging.getLogger(__name__)


class SessionSummarizer:
    """Service for creating session summaries."""

    @staticmethod
    def summarize_session(session_id: int) -> Optional[Dict[str, Any]]:
        """
        Create a summary of a session.
        Returns a dictionary with session statistics and key information.
        """
        with Session(engine) as session:
            db_session = session.get(DbSession, session_id)
            if not db_session:
                return None

            # Get messages
            messages = session.exec(
                select(Message).where(Message.session_id == session_id)
                .order_by(Message.timestamp.asc())
            ).all()

            # Get jobs
            jobs = session.exec(
                select(Job).where(Job.session_id == session_id)
            ).all()

            # Calculate statistics
            message_count = len(messages)
            job_count = len(jobs)
            completed_jobs = sum(1 for j in jobs if j.status == "completed")
            failed_jobs = sum(1 for j in jobs if j.status == "failed")

            # Get first and last message timestamps
            first_message_time = messages[0].timestamp if messages else None
            last_message_time = messages[-1].timestamp if messages else None

            # Calculate duration
            duration = None
            if first_message_time and last_message_time:
                duration = (last_message_time - first_message_time).total_seconds()

            # Create summary
            summary = {
                "session_id": session_id,
                "user_id": db_session.user_id,
                "created_at": db_session.created_at.isoformat(),
                "message_count": message_count,
                "job_count": job_count,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "duration_seconds": duration,
                "first_message_at": first_message_time.isoformat() if first_message_time else None,
                "last_message_at": last_message_time.isoformat() if last_message_time else None
            }

            # Add first and last messages (truncated)
            if messages:
                summary["first_message"] = messages[0].content[:100] + "..." if len(messages[0].content) > 100 else messages[0].content
                summary["last_message"] = messages[-1].content[:100] + "..." if len(messages[-1].content) > 100 else messages[-1].content

            # Add job statistics
            if jobs:
                summary["job_types"] = {}
                for job in jobs:
                    task_type = eval(job.task).get("type", "unknown")
                    summary["job_types"][task_type] = summary["job_types"].get(task_type, 0) + 1

            return summary

    @staticmethod
    def store_session_summary(session_id: int) -> Optional[MemoryItem]:
        """
        Create and store a summary of a session in memory.
        Returns the stored MemoryItem.
        """
        summary = SessionSummarizer.summarize_session(session_id)
        if not summary:
            return None

        with Session(engine) as session:
            # Store summary in memory
            memory_key = f"session_summary:{session_id}"
            db_item = MemoryItem(
                key=memory_key,
                value=str(summary),
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(db_item)
            session.commit()
            session.refresh(db_item)

            # Log the action
            audit_service.log(
                action=AuditAction.SESSION_SUMMARIZED,
                session_id=session_id,
                metadata={"session_id": session_id}
            )

            return db_item

    @staticmethod
    def summarize_recent_sessions(days: int = 1) -> List[Dict[str, Any]]:
        """
        Summarize all sessions from the last N days.
        Returns a list of summaries.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        with Session(engine) as session:
            db_sessions = session.exec(
                select(DbSession).where(DbSession.created_at >= cutoff)
            ).all()

            summaries = []
            for db_session in db_sessions:
                summary = SessionSummarizer.summarize_session(db_session.id)
                if summary:
                    summaries.append(summary)

            return summaries

    @staticmethod
    def get_session_summary(session_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored session summary.
        """
        with Session(engine) as session:
            memory_key = f"session_summary:{session_id}"
            db_item = session.exec(
                select(MemoryItem).where(MemoryItem.key == memory_key)
            ).first()

            if not db_item:
                return None

            return eval(db_item.value)

    @staticmethod
    def cleanup_old_summaries(days: int = 365) -> int:
        """
        Clean up old session summaries.
        Returns the number of summaries deleted.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        with Session(engine) as session:
            old_items = session.exec(
                select(MemoryItem)
                .where(
                    MemoryItem.key.startswith("session_summary:"),
                    MemoryItem.updated_at < cutoff
                )
            ).all()

            for item in old_items:
                session.delete(item)

            session.commit()
            deleted_count = len(old_items)
            logger.info(f"Cleaned up {deleted_count} old session summaries")
            return deleted_count


# Singleton instance
session_summarizer = SessionSummarizer()
