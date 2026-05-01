"""
Memory endpoints for PiGenus API.
Handles storage and retrieval of memory items.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional
from db.database import get_session
from db.models import MemoryItem, User, AuditLog
from models.schemas import (
    MemoryItemCreate,
    MemoryItemResponse,
    TokenData
)
from api.auth import get_current_user
from models.enums import AuditAction

router = APIRouter()


@router.post("/set", response_model=MemoryItemResponse)
async def set_memory_item(
    item: MemoryItemCreate,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Store a memory item.
    If the key already exists, it will be updated.
    """
    # Get the user from the database
    db_user = session.exec(
        select(User).where(User.username == current_user.username)
    ).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the memory item already exists
    db_item = session.exec(
        select(MemoryItem).where(MemoryItem.key == item.key)
    ).first()

    if db_item:
        # Update existing item
        db_item.value = str(item.value)
        db_item.updated_at = datetime.utcnow()
    else:
        # Create new item
        db_item = MemoryItem(
            key=item.key,
            value=str(item.value),
            user_id=db_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(db_item)

    session.commit()
    session.refresh(db_item)

    # Log the action
    session.add(AuditLog(
        action=AuditAction.MEMORY_SET,
        user_id=db_user.id,
        timestamp=datetime.utcnow(),
        metadata=f'{{"key": "{item.key}"}}'
    ))
    session.commit()

    return MemoryItemResponse(
        key=db_item.key,
        value=eval(db_item.value),
        created_at=db_item.created_at,
        updated_at=db_item.updated_at
    )


@router.get("/get/{key}", response_model=Optional[MemoryItemResponse])
async def get_memory_item(
    key: str,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieve a memory item by key.
    Returns None if the key doesn't exist.
    """
    # Get the user from the database
    db_user = session.exec(
        select(User).where(User.username == current_user.username)
    ).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get the memory item
    db_item = session.exec(
        select(MemoryItem).where(
            MemoryItem.key == key,
            MemoryItem.user_id == db_user.id
        )
    ).first()

    if not db_item:
        return None

    # Log the action
    session.add(AuditLog(
        action=AuditAction.MEMORY_GET,
        user_id=db_user.id,
        timestamp=datetime.utcnow(),
        metadata=f'{{"key": "{key}"}}'
    ))
    session.commit()

    return MemoryItemResponse(
        key=db_item.key,
        value=eval(db_item.value),
        created_at=db_item.created_at,
        updated_at=db_item.updated_at
    )


@router.get("/list")
async def list_memory_items(
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all memory items for the current user.
    """
    # Get the user from the database
    db_user = session.exec(
        select(User).where(User.username == current_user.username)
    ).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get all memory items for the user
    db_items = session.exec(
        select(MemoryItem).where(MemoryItem.user_id == db_user.id)
    ).all()

    return [
        MemoryItemResponse(
            key=item.key,
            value=eval(item.value),
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in db_items
    ]
