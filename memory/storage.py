"""
Memory storage service for PiGenus.
Handles long-term memory storage and retrieval.
"""
from sqlmodel import Session
from datetime import datetime
from typing import Optional, Dict, Any, List
from db.database import engine
from db.models import MemoryItem, User
from models.enums import AuditAction
from services.audit import audit_service
import logging

logger = logging.getLogger(__name__)


class MemoryStorage:
    """Service for storing and retrieving memory items."""

    @staticmethod
    def set(
        key: str,
        value: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> MemoryItem:
        """
        Store a memory item.
        If the key already exists, it will be updated.
        """
        with Session(engine) as session:
            # Check if item exists
            db_item = session.exec(
                select(MemoryItem).where(MemoryItem.key == key)
            ).first()

            if db_item:
                # Update existing
                db_item.value = str(value)
                db_item.updated_at = datetime.utcnow()
            else:
                # Create new
                db_item = MemoryItem(
                    key=key,
                    value=str(value),
                    user_id=user_id,
                    session_id=session_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(db_item)

            session.commit()
            session.refresh(db_item)

            # Log the action
            audit_service.log(
                action=AuditAction.MEMORY_SET,
                user_id=user_id,
                metadata={"key": key}
            )

            return db_item

    @staticmethod
    def get(key: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory item by key.
        Returns None if not found.
        """
        with Session(engine) as session:
            query = select(MemoryItem).where(MemoryItem.key == key)
            if user_id:
                query = query.where(MemoryItem.user_id == user_id)

            db_item = session.exec(query).first()

            if not db_item:
                return None

            # Log the action
            audit_service.log(
                action=AuditAction.MEMORY_GET,
                user_id=user_id,
                metadata={"key": key}
            )

            return eval(db_item.value)

    @staticmethod
    def delete(key: str, user_id: Optional[int] = None) -> bool:
        """
        Delete a memory item by key.
        Returns True if deleted, False if not found.
        """
        with Session(engine) as session:
            query = select(MemoryItem).where(MemoryItem.key == key)
            if user_id:
                query = query.where(MemoryItem.user_id == user_id)

            db_item = session.exec(query).first()

            if not db_item:
                return False

            session.delete(db_item)
            session.commit()

            # Log the action
            audit_service.log(
                action=AuditAction.MEMORY_SET,  # Using SET as DELETE isn't in enum
                user_id=user_id,
                metadata={"key": key, "action": "delete"}
            )

            return True

    @staticmethod
    def list_all(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all memory items.
        Optionally filter by user_id.
        """
        with Session(engine) as session:
            query = select(MemoryItem)
            if user_id:
                query = query.where(MemoryItem.user_id == user_id)

            db_items = session.exec(query).all()

            return [
                {
                    "key": item.key,
                    "value": eval(item.value),
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                for item in db_items
            ]

    @staticmethod
    def search(prefix: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for memory items by key prefix.
        """
        with Session(engine) as session:
            query = select(MemoryItem).where(MemoryItem.key.startswith(prefix))
            if user_id:
                query = query.where(MemoryItem.user_id == user_id)

            db_items = session.exec(query).all()

            return [
                {
                    "key": item.key,
                    "value": eval(item.value),
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                for item in db_items
            ]

    @staticmethod
    def cleanup_old_items(days: int = 365) -> int:
        """
        Clean up memory items older than specified days.
        Returns the number of items deleted.
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        with Session(engine) as session:
            old_items = session.exec(
                select(MemoryItem).where(MemoryItem.updated_at < cutoff)
            ).all()

            for item in old_items:
                session.delete(item)

            session.commit()
            deleted_count = len(old_items)
            logger.info(f"Cleaned up {deleted_count} old memory items")
            return deleted_count


# Singleton instance
memory_storage = MemoryStorage()
