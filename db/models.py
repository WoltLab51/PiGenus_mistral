"""
SQLModel entities for PiGenus database.
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from models.enums import JobStatus, WorkerStatus, UserRole, AuditAction

if TYPE_CHECKING:
    from db.database import Session


# ---------- User Model ---------- #
class User(SQLModel, table=True):
    """User entity for PiGenus."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=1, max_length=50)
    hashed_password: str = Field(min_length=60)  # bcrypt hash
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    workers: List["Worker"] = Relationship(back_populates="owner")
    sessions: List["Session"] = Relationship(back_populates="user")
    memory_items: List["MemoryItem"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


# ---------- Worker Model ---------- #
class Worker(SQLModel, table=True):
    """Worker entity for PiGenus."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=100)
    capabilities: str = Field(default="{}", description="JSON string of worker capabilities")
    status: WorkerStatus = Field(default=WorkerStatus.OFFLINE)
    last_heartbeat: Optional[datetime] = None
    owner_id: int = Field(foreign_key="user.id")

    # Relationships
    owner: User = Relationship(back_populates="workers")
    jobs: List["Job"] = Relationship(back_populates="worker")


# ---------- Session Model ---------- #
class Session(SQLModel, table=True):
    """Session entity for PiGenus."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="sessions")
    messages: List["Message"] = Relationship(back_populates="session")
    jobs: List["Job"] = Relationship(back_populates="session")
    memory_items: List["MemoryItem"] = Relationship(back_populates="session")


# ---------- Message Model ---------- #
class Message(SQLModel, table=True):
    """Message entity for PiGenus sessions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    content: str = Field(min_length=1)
    role: str = Field(min_length=1, max_length=20)  # "user", "assistant", "system"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    session: Session = Relationship(back_populates="messages")


# ---------- Job Model ---------- #
class Job(SQLModel, table=True):
    """Job entity for PiGenus task queue."""
    id: Optional[int] = Field(default=None, primary_key=True)
    task: str = Field(description="JSON string of task payload")
    status: JobStatus = Field(default=JobStatus.PENDING)
    priority: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    leased_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = Field(default=None, description="JSON string of job result")
    worker_id: Optional[int] = Field(default=None, foreign_key="worker.id")
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")

    # Relationships
    worker: Optional[Worker] = Relationship(back_populates="jobs")
    session: Optional[Session] = Relationship(back_populates="jobs")
    events: List["JobEvent"] = Relationship(back_populates="job")


# ---------- JobEvent Model ---------- #
class JobEvent(SQLModel, table=True):
    """Job event entity for tracking job lifecycle."""
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    event_type: str = Field(min_length=1, max_length=50)  # "leased", "started", "failed", etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = Field(default=None, description="JSON string of event details")

    # Relationships
    job: Job = Relationship(back_populates="events")


# ---------- MemoryItem Model ---------- #
class MemoryItem(SQLModel, table=True):
    """Memory item entity for long-term storage."""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, min_length=1, max_length=255)
    value: str = Field(description="JSON string of memory value")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="memory_items")
    session: Optional[Session] = Relationship(back_populates="memory_items")


# ---------- AuditLog Model ---------- #
class AuditLog(SQLModel, table=True):
    """Audit log entity for tracking system actions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    action: AuditAction
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    worker_id: Optional[int] = Field(default=None, foreign_key="worker.id")
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[str] = Field(default=None, description="JSON string of additional metadata")

    # Relationships
    user: Optional[User] = Relationship(back_populates="audit_logs")
