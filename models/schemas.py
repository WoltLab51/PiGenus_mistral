"""
Pydantic schemas for PiGenus API requests and responses.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from .enums import JobStatus, WorkerStatus, UserRole


# ---------- User Schemas ---------- #
class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    is_admin: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime


# ---------- Worker Schemas ---------- #
class WorkerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class WorkerCreate(WorkerBase):
    pass


class WorkerResponse(WorkerBase):
    id: int
    status: WorkerStatus
    last_heartbeat: Optional[datetime] = None
    owner_id: int


class WorkerHeartbeat(BaseModel):
    worker_id: int


# ---------- Job Schemas ---------- #
class JobBase(BaseModel):
    task: Dict[str, Any] = Field(..., description="Task payload as JSON")
    priority: int = Field(default=0, ge=0)


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    status: JobStatus
    created_at: datetime
    leased_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[int] = None
    result: Optional[Dict[str, Any]] = None


class JobLeaseResponse(BaseModel):
    job: JobResponse
    lease_expires_at: datetime


class JobAck(BaseModel):
    result: Dict[str, Any] = Field(..., description="Job result as JSON")


class JobFail(BaseModel):
    error: str = Field(..., description="Error message")


# ---------- Memory Schemas ---------- #
class MemoryItemBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Dict[str, Any] = Field(..., description="Memory value as JSON")


class MemoryItemCreate(MemoryItemBase):
    pass


class MemoryItemResponse(MemoryItemBase):
    created_at: datetime
    updated_at: datetime


# ---------- Auth Schemas ---------- #
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    is_admin: bool = False


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


# ---------- Admin Schemas ---------- #
class WorkerStatusResponse(BaseModel):
    worker_id: int
    name: str
    status: WorkerStatus
    last_heartbeat: Optional[datetime] = None
    owner: str


class JobStatusResponse(BaseModel):
    job_id: int
    status: JobStatus
    priority: int
    created_at: datetime
    worker_id: Optional[int] = None


class AdminStatusResponse(BaseModel):
    workers: List[WorkerStatusResponse]
    jobs: List[JobStatusResponse]
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_workers: int
    online_workers: int


# ---------- Health Schemas ---------- #
class HealthResponse(BaseModel):
    status: str
    details: Dict[str, Any]
    timestamp: datetime
