"""
Enums for PiGenus models.
"""
from enum import Enum


class JobStatus(str, Enum):
    """Status of a job in the queue."""
    PENDING = "pending"
    LEASED = "leased"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class WorkerStatus(str, Enum):
    """Status of a worker."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class UserRole(str, Enum):
    """Role of a user."""
    USER = "user"
    ADMIN = "admin"


class AuditAction(str, Enum):
    """Actions for audit logging."""
    # Worker actions
    WORKER_REGISTERED = "worker_registered"
    WORKER_HEARTBEAT = "worker_heartbeat"
    WORKER_OFFLINE = "worker_offline"

    # Job actions
    JOB_SUBMITTED = "job_submitted"
    JOB_LEASED = "job_leased"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_REQUEUED = "job_requeued"

    # Memory actions
    MEMORY_SET = "memory_set"
    MEMORY_GET = "memory_get"

    # System actions
    BACKUP_CREATED = "backup_created"
    LOGS_ROTATED = "logs_rotated"
    SESSION_SUMMARIZED = "session_summarized"
