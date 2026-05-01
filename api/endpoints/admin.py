"""
Admin endpoints for PiGenus API.
Provides status and management endpoints for administrators.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from datetime import datetime
from typing import List
from db.database import get_session
from db.models import Worker, Job, AuditLog, User
from models.schemas import (
    AdminStatusResponse,
    WorkerStatusResponse,
    JobStatusResponse,
    TokenData
)
from api.auth import get_current_admin_user
from models.enums import JobStatus, WorkerStatus

router = APIRouter()


@router.get("/status", response_model=AdminStatusResponse)
async def get_admin_status(
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Get the current status of the PiGenus system.
    Returns information about workers, jobs, and system health.
    """
    # Get all workers
    db_workers = session.exec(select(Worker)).all()
    workers = [
        WorkerStatusResponse(
            worker_id=w.id,
            name=w.name,
            status=w.status,
            last_heartbeat=w.last_heartbeat,
            owner=w.owner.username
        )
        for w in db_workers
    ]

    # Get all jobs
    db_jobs = session.exec(select(Job)).all()
    jobs = [
        JobStatusResponse(
            job_id=j.id,
            status=j.status,
            priority=j.priority,
            created_at=j.created_at,
            worker_id=j.worker_id
        )
        for j in db_jobs
    ]

    # Get job statistics
    pending_jobs = session.exec(
        select(func.count()).where(Job.status == JobStatus.PENDING)
    ).one()
    running_jobs = session.exec(
        select(func.count()).where(Job.status == JobStatus.RUNNING)
    ).one()
    completed_jobs = session.exec(
        select(func.count()).where(Job.status == JobStatus.COMPLETED)
    ).one()
    failed_jobs = session.exec(
        select(func.count()).where(Job.status == JobStatus.FAILED)
    ).one()

    # Get worker statistics
    total_workers = len(db_workers)
    online_workers = session.exec(
        select(func.count()).where(Worker.status == WorkerStatus.ONLINE)
    ).one()

    return AdminStatusResponse(
        workers=workers,
        jobs=jobs,
        pending_jobs=pending_jobs,
        running_jobs=running_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        total_workers=total_workers,
        online_workers=online_workers
    )


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Get recent audit logs.
    """
    db_logs = session.exec(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "user_id": log.user_id,
            "worker_id": log.worker_id,
            "job_id": log.job_id,
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.metadata
        }
        for log in db_logs
    ]


@router.get("/users")
async def get_users(
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    List all users (admin only).
    """
    db_users = session.exec(select(User)).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat()
        }
        for user in db_users
    ]
