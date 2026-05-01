"""
Job endpoints for PiGenus API.
Handles job submission, leasing, acknowledgment, and failure reporting.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
from db.database import get_session
from db.models import Job, Worker, JobEvent, AuditLog, Session as DbSession
from models.schemas import (
    JobCreate,
    JobResponse,
    JobLeaseResponse,
    JobAck,
    JobFail,
    TokenData
)
from api.auth import get_current_user
from models.enums import JobStatus, WorkerStatus, AuditAction
from core.config import settings

router = APIRouter()


@router.post("/submit", response_model=JobResponse)
async def submit_job(
    job: JobCreate,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Submit a new job to the queue.
    """
    # Create the job
    db_job = Job(
        task=str(job.task),
        priority=job.priority,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    # Log the submission
    session.add(AuditLog(
        action=AuditAction.JOB_SUBMITTED,
        user_id=None,  # TODO: Link to user once User model is fully integrated
        job_id=db_job.id,
        timestamp=datetime.utcnow(),
        metadata=f'{{"task": {job.task}, "priority": {job.priority}}}'
    ))
    session.commit()

    return JobResponse(
        id=db_job.id,
        task=job.task,
        status=db_job.status,
        priority=db_job.priority,
        created_at=db_job.created_at,
        leased_at=None,
        completed_at=None,
        worker_id=None,
        result=None
    )


@router.get("/lease", response_model=Optional[JobLeaseResponse])
async def lease_job(
    worker_id: int,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Lease the next available job for a worker.
    Returns the job and lease expiration time.
    """
    # Get the worker
    db_worker = session.get(Worker, worker_id)
    if not db_worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )

    # Verify the worker belongs to the current user
    if db_worker.owner.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to lease jobs for this worker"
        )

    # Set worker to BUSY
    db_worker.status = WorkerStatus.BUSY
    session.add(db_worker)

    # Find the next pending job (highest priority first, then oldest)
    db_job = session.exec(
        select(Job)
        .where(Job.status == JobStatus.PENDING)
        .order_by(Job.priority.desc(), Job.created_at.asc())
        .limit(1)
    ).first()

    if not db_job:
        # No jobs available, set worker back to ONLINE
        db_worker.status = WorkerStatus.ONLINE
        session.add(db_worker)
        session.commit()
        return None

    # Lease the job
    db_job.status = JobStatus.LEASED
    db_job.leased_at = datetime.utcnow()
    db_job.worker_id = worker_id
    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    # Add job event
    session.add(JobEvent(
        job_id=db_job.id,
        event_type="leased",
        timestamp=datetime.utcnow(),
        details=f'{{"worker_id": {worker_id}}}'
    ))

    # Log the lease
    session.add(AuditLog(
        action=AuditAction.JOB_LEASED,
        worker_id=worker_id,
        job_id=db_job.id,
        timestamp=datetime.utcnow()
    ))
    session.commit()

    return JobLeaseResponse(
        job=JobResponse(
            id=db_job.id,
            task=eval(db_job.task),
            status=db_job.status,
            priority=db_job.priority,
            created_at=db_job.created_at,
            leased_at=db_job.leased_at,
            completed_at=db_job.completed_at,
            worker_id=db_job.worker_id,
            result=eval(db_job.result) if db_job.result else None
        ),
        lease_expires_at=datetime.utcnow() + timedelta(
            seconds=settings.worker_lease_timeout
        )
    )


@router.post("/{job_id}/ack")
async def acknowledge_job(
    job_id: int,
    ack: JobAck,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Acknowledge successful completion of a job.
    """
    db_job = session.get(Job, job_id)
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify the job's worker belongs to the current user
    if db_job.worker and db_job.worker.owner.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to acknowledge this job"
        )

    # Update job
    db_job.status = JobStatus.COMPLETED
    db_job.completed_at = datetime.utcnow()
    db_job.result = str(ack.result)
    session.add(db_job)

    # Add job event
    session.add(JobEvent(
        job_id=job_id,
        event_type="completed",
        timestamp=datetime.utcnow(),
        details=f'{{"result": {ack.result}}}'
    ))

    # Set worker back to ONLINE
    if db_job.worker:
        db_job.worker.status = WorkerStatus.ONLINE
        session.add(db_job.worker)

    # Log the completion
    session.add(AuditLog(
        action=AuditAction.JOB_COMPLETED,
        worker_id=db_job.worker_id,
        job_id=job_id,
        timestamp=datetime.utcnow()
    ))
    session.commit()

    return {"status": "acknowledged", "job_id": job_id}


@router.post("/{job_id}/fail")
async def fail_job(
    job_id: int,
    fail: JobFail,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Report failure of a job.
    """
    db_job = session.get(Job, job_id)
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify the job's worker belongs to the current user
    if db_job.worker and db_job.worker.owner.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to fail this job"
        )

    # Update job
    db_job.status = JobStatus.FAILED
    db_job.completed_at = datetime.utcnow()
    session.add(db_job)

    # Add job event
    session.add(JobEvent(
        job_id=job_id,
        event_type="failed",
        timestamp=datetime.utcnow(),
        details=f'{{"error": "{fail.error}"}}'
    ))

    # Set worker back to ONLINE
    if db_job.worker:
        db_job.worker.status = WorkerStatus.ONLINE
        session.add(db_job.worker)

    # Log the failure
    session.add(AuditLog(
        action=AuditAction.JOB_FAILED,
        worker_id=db_job.worker_id,
        job_id=job_id,
        timestamp=datetime.utcnow(),
        metadata=f'{{"error": "{fail.error}"}}'
    ))
    session.commit()

    return {"status": "failed", "job_id": job_id, "error": fail.error}


@router.get("/list", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = None,
    worker_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List jobs with optional filters.
    """
    query = select(Job)

    # Filter by status if provided
    if status:
        query = query.where(Job.status == status)

    # Filter by worker_id if provided
    if worker_id:
        query = query.where(Job.worker_id == worker_id)

    # Get all jobs (TODO: Add user filtering once Job model is linked to User)
    db_jobs = session.exec(query).all()

    return [
        JobResponse(
            id=j.id,
            task=eval(j.task),
            status=j.status,
            priority=j.priority,
            created_at=j.created_at,
            leased_at=j.leased_at,
            completed_at=j.completed_at,
            worker_id=j.worker_id,
            result=eval(j.result) if j.result else None
        )
        for j in db_jobs
    ]
