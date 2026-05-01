"""
Health check utilities for PiGenus.
"""
from sqlmodel import Session
from db.database import get_session
from db.models import Job, Worker, JobStatus, WorkerStatus
from datetime import datetime, timedelta
from typing import Dict, Any
import psutil
import os


class HealthChecker:
    """Service for performing health checks."""

    @staticmethod
    def check_database(session: Session) -> Dict[str, Any]:
        """Check database connectivity and status."""
        try:
            session.exec("SELECT 1")
            return {
                "status": "healthy",
                "details": {
                    "connection": "ok"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "details": {
                    "error": str(e)
                }
            }

    @staticmethod
    def check_disk() -> Dict[str, Any]:
        """Check disk space and health."""
        try:
            disk = psutil.disk_usage("/")
            free_mb = disk.free // (1024 * 1024)
            return {
                "status": "healthy" if free_mb > 100 else "low_disk",
                "details": {
                    "total_gb": disk.total // (1024 ** 3),
                    "used_gb": disk.used // (1024 ** 3),
                    "free_gb": disk.free // (1024 ** 3),
                    "free_mb": free_mb,
                    "usage_percent": disk.percent
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    @staticmethod
    def check_memory() -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            mem = psutil.virtual_memory()
            return {
                "status": "healthy" if mem.percent < 90 else "high_memory",
                "details": {
                    "total_gb": mem.total // (1024 ** 3),
                    "available_gb": mem.available // (1024 ** 3),
                    "used_gb": mem.used // (1024 ** 3),
                    "usage_percent": mem.percent
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    @staticmethod
    def check_workers(session: Session) -> Dict[str, Any]:
        """Check worker status and health."""
        try:
            workers = session.exec(select(Worker)).all()
            online_count = sum(1 for w in workers if w.status == WorkerStatus.ONLINE)
            offline_count = sum(1 for w in workers if w.status == WorkerStatus.OFFLINE)
            busy_count = sum(1 for w in workers if w.status == WorkerStatus.BUSY)

            # Check for stale workers (no heartbeat for >5 minutes)
            stale_workers = [
                w for w in workers
                if w.status == WorkerStatus.ONLINE and
                w.last_heartbeat and
                (datetime.utcnow() - w.last_heartbeat) > timedelta(minutes=5)
            ]

            return {
                "status": "healthy" if offline_count == 0 and len(stale_workers) == 0 else "degraded",
                "details": {
                    "total": len(workers),
                    "online": online_count,
                    "offline": offline_count,
                    "busy": busy_count,
                    "stale": len(stale_workers)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    @staticmethod
    def check_jobs(session: Session) -> Dict[str, Any]:
        """Check job queue status."""
        try:
            jobs = session.exec(select(Job)).all()
            pending = sum(1 for j in jobs if j.status == JobStatus.PENDING)
            leased = sum(1 for j in jobs if j.status == JobStatus.LEASED)
            running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
            completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
            timeout = sum(1 for j in jobs if j.status == JobStatus.TIMEOUT)

            # Check for stuck jobs (leased for >2 minutes)
            stuck_jobs = [
                j for j in jobs
                if j.status == JobStatus.LEASED and
                j.leased_at and
                (datetime.utcnow() - j.leased_at) > timedelta(minutes=2)
            ]

            return {
                "status": "healthy" if len(stuck_jobs) == 0 else "degraded",
                "details": {
                    "total": len(jobs),
                    "pending": pending,
                    "leased": leased,
                    "running": running,
                    "completed": completed,
                    "failed": failed,
                    "timeout": timeout,
                    "stuck": len(stuck_jobs)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    @staticmethod
    def get_full_health_report(session: Session) -> Dict[str, Any]:
        """Get a comprehensive health report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": HealthChecker.check_database(session),
            "disk": HealthChecker.check_disk(),
            "memory": HealthChecker.check_memory(),
            "workers": HealthChecker.check_workers(session),
            "jobs": HealthChecker.check_jobs(session)
        }

    @staticmethod
    def get_overall_status(health_report: Dict[str, Any]) -> str:
        """Determine overall status from health report."""
        statuses = [
            health_report["database"]["status"],
            health_report["disk"]["status"],
            health_report["memory"]["status"],
            health_report["workers"]["status"],
            health_report["jobs"]["status"]
        ]

        if "unhealthy" in statuses or "error" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
