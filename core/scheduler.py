"""
Scheduler for PiGenus nightly jobs.
Handles backup, cleanup, and maintenance tasks.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session
from datetime import datetime, timedelta
import logging
import shutil
import os
from db.database import engine
from db.models import Job, JobStatus, JobEvent, AuditLog, Session as DbSession
from core.config import settings

logger = logging.getLogger(__name__)


def rotate_logs():
    """Rotate application logs."""
    log_file = "pigenus.log"
    if os.path.exists(log_file):
        try:
            # Rotate up to 5 log files
            for i in range(4, 0, -1):
                if os.path.exists(f"{log_file}.{i}"):
                    shutil.move(f"{log_file}.{i}", f"{log_file}.{i+1}")
            shutil.move(log_file, f"{log_file}.1")
            logger.info("Logs rotated")
        except Exception as e:
            logger.error(f"Failed to rotate logs: {e}")
    else:
        logger.debug("No log file to rotate")


def backup_database():
    """Create a backup of the SQLite database."""
    db_path = settings.database_url.replace("sqlite:///", "")
    if not db_path or db_path == ":memory:":
        logger.debug("No database to backup (in-memory)")
        return

    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"pigenus_{timestamp}.db")

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")

        # Clean up old backups (keep last 7 days)
        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if datetime.utcnow() - file_time > timedelta(days=7):
                    os.remove(filepath)
                    logger.info(f"Removed old backup: {filename}")
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")


def requeue_stuck_jobs():
    """Requeue jobs that are stuck in LEASED status."""
    with Session(engine) as session:
        # Find jobs stuck in LEASED for too long
        stuck_jobs = session.exec(
            select(Job).where(
                Job.status == JobStatus.LEASED,
                Job.leased_at < datetime.utcnow() - timedelta(seconds=settings.worker_lease_timeout)
            )
        ).all()

        for job in stuck_jobs:
            job.status = JobStatus.PENDING
            job.leased_at = None
            job.worker_id = None
            session.add(job)

            # Add job event
            session.add(JobEvent(
                job_id=job.id,
                event_type="requeued",
                timestamp=datetime.utcnow(),
                details="Job was stuck in LEASED state"
            ))

            # Log the action
            session.add(AuditLog(
                action="job_requeued",
                job_id=job.id,
                timestamp=datetime.utcnow()
            ))

        session.commit()
        logger.info(f"Requeued {len(stuck_jobs)} stuck jobs")


def summarize_sessions():
    """Create summaries for recent sessions."""
    with Session(engine) as session:
        # Get sessions from the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        sessions = session.exec(
            select(DbSession).where(DbSession.created_at >= yesterday)
        ).all()

        for session in sessions:
            # Count messages in session
            message_count = session.exec(
                select(func.count()).where(Message.session_id == session.id)
            ).one()

            # Count jobs in session
            job_count = session.exec(
                select(func.count()).where(Job.session_id == session.id)
            ).one()

            # Here you could add AI summarization
            # For now, just log the session stats
            logger.info(
                f"Session {session.id}: "
                f"{message_count} messages, {job_count} jobs"
            )

            # TODO: Store summary in MemoryItem or Session table


def cleanup_old_jobs():
    """Clean up old completed/failed jobs."""
    with Session(engine) as session:
        # Delete jobs older than 30 days (keep recent for audit)
        cutoff = datetime.utcnow() - timedelta(days=30)
        old_jobs = session.exec(
            select(Job).where(
                Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                Job.completed_at < cutoff
            )
        ).all()

        for job in old_jobs:
            session.delete(job)

        session.commit()
        logger.info(f"Cleaned up {len(old_jobs)} old jobs")


def nightly_jobs():
    """Run all nightly maintenance jobs."""
    logger.info("Running nightly jobs...")

    rotate_logs()
    backup_database()
    requeue_stuck_jobs()
    summarize_sessions()
    cleanup_old_jobs()

    logger.info("Nightly jobs completed")


def start_scheduler():
    """Start the background scheduler for nightly jobs."""
    scheduler = BackgroundScheduler()

    # Run nightly jobs at configured hour
    scheduler.add_job(
        nightly_jobs,
        CronTrigger(
            hour=settings.nightly_jobs_hour,
            minute=0
        ),
        id="nightly_jobs",
        name="Run nightly maintenance jobs",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started (nightly jobs at {settings.nightly_jobs_hour}:00 UTC)")

    # Keep the scheduler running
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    start_scheduler()
