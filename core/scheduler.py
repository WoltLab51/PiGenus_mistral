"""
Scheduler for PiGenus nightly jobs.
Handles backup, cleanup, and maintenance tasks.

KONTINUITÄT: Läuft dauerhaft, verlässlich und ressourcenschonend.
Dieser Scheduler stellt sicher, dass PiGenus seine Hintergrundaufgaben
regelmäßig und zuverlässig ausführt.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, func, select
from datetime import datetime, timedelta
import logging
import shutil
import os
from db.database import engine
from db.models import Job, JobStatus, JobEvent, AuditLog, Session as DbSession, Message
from core.config import settings
from core.philosophy import PiGenusPrinciple

logger = logging.getLogger(__name__)


def rotate_logs():
    """
    Rotiert Anwendungs-Logs (KONTINUITÄT: Regelmäßige Wartung).
    """
    log_file = "pigenus.log"
    if os.path.exists(log_file):
        try:
            # Rotiert bis zu 5 Log-Dateien
            for i in range(4, 0, -1):
                if os.path.exists(f"{log_file}.{i}"):
                    shutil.move(f"{log_file}.{i}", f"{log_file}.{i+1}")
            shutil.move(log_file, f"{log_file}.1")
            logger.info("Logs rotated (KONTINUITÄT)")
        except Exception as e:
            logger.error(f"Failed to rotate logs: {e}")
    else:
        logger.debug("No log file to rotate")


def backup_database():
    """
    Erstellt ein Backup der SQLite-Datenbank (KONTINUITÄT: Datensicherheit).
    """
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
        logger.info(f"Database backup created: {backup_path} (KONTINUITÄT)")

        # Alte Backups bereinigen (letzte 7 Tage behalten)
        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if datetime.utcnow() - file_time > timedelta(days=7):
                    os.remove(filepath)
                    logger.info(f"Removed old backup: {filename} (KONTINUITÄT)")
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")


def requeue_stuck_jobs():
    """
    Setzt Jobs, die zu lange im LEASED-Status sind, zurück auf PENDING (ORCHESTRIERUNG: Job-Koordination).
    """
    with Session(engine) as session:
        # Jobs finden, die zu lange im LEASED-Status sind
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

            # Job-Event hinzufügen (ORCHESTRIERUNG)
            session.add(JobEvent(
                job_id=job.id,
                event_type="requeued",
                timestamp=datetime.utcnow(),
                details="Job was stuck in LEASED state (ORCHESTRIERUNG)"
            ))

            # Audit-Log (ADMINISTRATION)
            session.add(AuditLog(
                action="job_requeued",
                job_id=job.id,
                timestamp=datetime.utcnow()
            ))

        session.commit()
        logger.info(f"Requeued {len(stuck_jobs)} stuck jobs (ORCHESTRIERUNG)")


def summarize_sessions():
    """
    Erstellt Zusammenfassungen für aktuelle Sessions (PERSISTENZ: Wissensverdichtung).
    """
    with Session(engine) as session:
        # Sessions der letzten 24 Stunden
        yesterday = datetime.utcnow() - timedelta(days=1)
        db_sessions = session.exec(
            select(DbSession).where(DbSession.created_at >= yesterday)
        ).all()

        for db_session in db_sessions:
            # Nachrichten in der Session zählen (PERSISTENZ)
            message_count = session.exec(
                select(func.count()).where(Message.session_id == db_session.id)
            ).one()

            # Jobs in der Session zählen (ORCHESTRIERUNG)
            job_count = session.exec(
                select(func.count()).where(Job.session_id == db_session.id)
            ).one()

            logger.info(
                f"Session {db_session.id}: {message_count} messages, {job_count} jobs (PERSISTENZ)"
            )
            # TODO: Hier könnte eine KI-Zusammenfassung erstellt werden


def cleanup_old_jobs():
    """
    Bereinigt alte abgeschlossene Jobs (ADMINISTRATION: Systempflege).
    """
    with Session(engine) as session:
        # Jobs älter als 30 Tage löschen (ADMINISTRATION)
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
        logger.info(f"Cleaned up {len(old_jobs)} old jobs (ADMINISTRATION)")


def nightly_jobs():
    """
    Führt alle Nachtjobs aus (KONTINUITÄT: Regelmäßige Wartung).
    
    Diese Funktion wird täglich um 3 Uhr UTC ausgeführt und stellt sicher,
    dass PiGenus seine Hintergrundaufgaben zuverlässig erledigt.
    """
    logger.info("Running nightly jobs (KONTINUITÄT)...")

    # PERSISTENZ: Backups sichern
    backup_database()

    # KONTINUITÄT: Logs rotieren
    rotate_logs()

    # ORCHESTRIERUNG: Stuck Jobs requeuen
    requeue_stuck_jobs()

    # PERSISTENZ: Wissensverdichtung (Session-Zusammenfassungen)
    summarize_sessions()

    # ADMINISTRATION: Alte Jobs bereinigen
    cleanup_old_jobs()

    logger.info("Nightly jobs completed (KONTINUITÄT)")


def start_scheduler():
    """
    Startet den Hintergrund-Scheduler für Nachtjobs (KONTINUITÄT: Dauerhafter Betrieb).
    
    Der Scheduler läuft als separater Prozess und führt die Nachtjobs
    zur konfigurierten Uhrzeit aus.
    """
    scheduler = BackgroundScheduler()

    # Nachtjobs zur konfigurierten Stunde ausführen
    scheduler.add_job(
        nightly_jobs,
        CronTrigger(
            hour=settings.nightly_jobs_hour,
            minute=0
        ),
        id="nightly_jobs",
        name="Run nightly maintenance jobs (KONTINUITÄT)",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started (nightly jobs at {settings.nightly_jobs_hour}:00 UTC) (KONTINUITÄT)")

    # Scheduler am Laufen halten
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped (KONTINUITÄT)")


if __name__ == "__main__":
    start_scheduler()
