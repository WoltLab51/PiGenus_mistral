"""
Worker endpoints for PiGenus API.
Handles worker registration, heartbeat, and listing.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import List
from db.database import get_session
from db.models import Worker, User, AuditLog
from models.schemas import (
    WorkerCreate,
    WorkerResponse,
    WorkerHeartbeat,
    TokenData
)
from api.auth import get_current_user
from models.enums import AuditAction, WorkerStatus

router = APIRouter()


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    worker: WorkerCreate,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Register a new worker.
    The worker will be associated with the current authenticated user.
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

    # Create the worker
    db_worker = Worker(
        name=worker.name,
        capabilities=str(worker.capabilities),
        status=WorkerStatus.ONLINE,
        last_heartbeat=datetime.utcnow(),
        owner_id=db_user.id
    )
    session.add(db_worker)
    session.commit()
    session.refresh(db_worker)

    # Log the registration
    session.add(AuditLog(
        action=AuditAction.WORKER_REGISTERED,
        user_id=db_user.id,
        worker_id=db_worker.id,
        timestamp=datetime.utcnow(),
        metadata=f'{{"name": "{worker.name}", "capabilities": {worker.capabilities}}}'
    ))
    session.commit()

    return WorkerResponse(
        id=db_worker.id,
        name=db_worker.name,
        capabilities=worker.capabilities,
        status=db_worker.status,
        last_heartbeat=db_worker.last_heartbeat,
        owner_id=db_worker.owner_id
    )


@router.post("/heartbeat", response_model=WorkerResponse)
async def worker_heartbeat(
    heartbeat: WorkerHeartbeat,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update worker heartbeat to indicate it's still alive.
    """
    # Get the worker
    db_worker = session.get(Worker, heartbeat.worker_id)
    if not db_worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )

    # Verify the worker belongs to the current user
    if db_worker.owner.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this worker"
        )

    # Update heartbeat
    db_worker.last_heartbeat = datetime.utcnow()
    db_worker.status = WorkerStatus.ONLINE
    session.add(db_worker)
    session.commit()
    session.refresh(db_worker)

    # Log the heartbeat
    session.add(AuditLog(
        action=AuditAction.WORKER_HEARTBEAT,
        user_id=db_worker.owner_id,
        worker_id=db_worker.id,
        timestamp=datetime.utcnow()
    ))
    session.commit()

    return WorkerResponse(
        id=db_worker.id,
        name=db_worker.name,
        capabilities=eval(db_worker.capabilities),
        status=db_worker.status,
        last_heartbeat=db_worker.last_heartbeat,
        owner_id=db_worker.owner_id
    )


@router.get("/list", response_model=List[WorkerResponse])
async def list_workers(
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all workers owned by the current user.
    """
    # Get all workers for the current user
    db_workers = session.exec(
        select(Worker).where(Worker.owner.username == current_user.username)
    ).all()

    return [
        WorkerResponse(
            id=w.id,
            name=w.name,
            capabilities=eval(w.capabilities),
            status=w.status,
            last_heartbeat=w.last_heartbeat,
            owner_id=w.owner_id
        )
        for w in db_workers
    ]
