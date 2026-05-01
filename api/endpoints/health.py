"""
Health check endpoint for PiGenus.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from db.database import get_session
from datetime import datetime
import psutil
import shutil
import os

router = APIRouter()


@router.get("/health")
async def health_check(session: Session = Depends(get_session)):
    """
    Health check endpoint for PiGenus.
    Returns the status of the database, disk, and memory.
    """
    # Database check
    try:
        session.exec("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Disk check
    try:
        disk = psutil.disk_usage("/")
        disk_free_mb = disk.free // (1024 * 1024)
        disk_status = "healthy" if disk_free_mb > 100 else "low_disk"
    except Exception as e:
        disk_status = f"error: {str(e)}"
        disk_free_mb = 0

    # Memory check
    try:
        mem = psutil.virtual_memory()
        mem_status = "healthy" if mem.percent < 90 else "high_memory"
    except Exception as e:
        mem_status = f"error: {str(e)}"
        mem.percent = 0

    # Overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in [db_status, disk_status, mem_status]
    ) else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "database": db_status,
            "disk": {
                "status": disk_status,
                "free_mb": disk_free_mb
            },
            "memory": {
                "status": mem_status,
                "usage_percent": mem.percent
            }
        }
    }
