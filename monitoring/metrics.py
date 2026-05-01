"""
Prometheus metrics for PiGenus.
Optional module for monitoring with Prometheus.
"""
try:
    from prometheus_client import start_http_server, Gauge, Counter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Metrics definitions
if PROMETHEUS_AVAILABLE:
    # System metrics
    SYSTEM_CPU_USAGE = Gauge('pigenus_cpu_usage_percent', 'CPU usage percentage')
    SYSTEM_MEMORY_USAGE = Gauge('pigenus_memory_usage_percent', 'Memory usage percentage')
    SYSTEM_DISK_USAGE = Gauge('pigenus_disk_usage_percent', 'Disk usage percentage')

    # Database metrics
    DB_CONNECTIONS = Gauge('pigenus_db_connections', 'Active database connections')
    DB_QUERY_TIME = Gauge('pigenus_db_query_time_seconds', 'Database query time')

    # Worker metrics
    WORKER_TOTAL = Gauge('pigenus_worker_total', 'Total registered workers')
    WORKER_ONLINE = Gauge('pigenus_worker_online', 'Online workers')
    WORKER_OFFLINE = Gauge('pigenus_worker_offline', 'Offline workers')
    WORKER_BUSY = Gauge('pigenus_worker_busy', 'Busy workers')

    # Job metrics
    JOB_TOTAL = Gauge('pigenus_job_total', 'Total jobs')
    JOB_PENDING = Gauge('pigenus_job_pending', 'Pending jobs')
    JOB_LEASED = Gauge('pigenus_job_leased', 'Leased jobs')
    JOB_RUNNING = Gauge('pigenus_job_running', 'Running jobs')
    JOB_COMPLETED = Gauge('pigenus_job_completed', 'Completed jobs')
    JOB_FAILED = Gauge('pigenus_job_failed', 'Failed jobs')
    JOB_TIMEOUT = Gauge('pigenus_job_timeout', 'Timeout jobs')

    # API metrics
    API_REQUESTS = Counter(
        'pigenus_api_requests_total',
        'Total API requests',
        ['method', 'endpoint', 'status']
    )
    API_REQUEST_TIME = Gauge(
        'pigenus_api_request_time_seconds',
        'API request time',
        ['method', 'endpoint']
    )

    # Audit metrics
    AUDIT_LOGS = Counter(
        'pigenus_audit_logs_total',
        'Total audit log entries',
        ['action']
    )


class MetricsService:
    """Service for managing Prometheus metrics."""

    @staticmethod
    def start_metrics_server(port: int = 9000) -> bool:
        """Start the Prometheus metrics HTTP server."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not installed. Install with: pip install prometheus-client")
            return False

        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            return False

    @staticmethod
    def update_system_metrics():
        """Update system-related metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            SYSTEM_CPU_USAGE.set(cpu)
            SYSTEM_MEMORY_USAGE.set(mem.percent)
            SYSTEM_DISK_USAGE.set(disk.percent)
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    @staticmethod
    def update_worker_metrics(online: int, offline: int, busy: int, total: int):
        """Update worker-related metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        WORKER_TOTAL.set(total)
        WORKER_ONLINE.set(online)
        WORKER_OFFLINE.set(offline)
        WORKER_BUSY.set(busy)

    @staticmethod
    def update_job_metrics(
        pending: int,
        leased: int,
        running: int,
        completed: int,
        failed: int,
        timeout: int,
        total: int
    ):
        """Update job-related metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        JOB_TOTAL.set(total)
        JOB_PENDING.set(pending)
        JOB_LEASED.set(leased)
        JOB_RUNNING.set(running)
        JOB_COMPLETED.set(completed)
        JOB_FAILED.set(failed)
        JOB_TIMEOUT.set(timeout)

    @staticmethod
    def increment_api_request(method: str, endpoint: str, status: int):
        """Increment API request counter."""
        if not PROMETHEUS_AVAILABLE:
            return

        API_REQUESTS.labels(method=method, endpoint=endpoint, status=status).inc()

    @staticmethod
    def set_api_request_time(method: str, endpoint: str, time: float):
        """Set API request time gauge."""
        if not PROMETHEUS_AVAILABLE:
            return

        API_REQUEST_TIME.labels(method=method, endpoint=endpoint).set(time)

    @staticmethod
    def increment_audit_log(action: str):
        """Increment audit log counter."""
        if not PROMETHEUS_AVAILABLE:
            return

        AUDIT_LOGS.labels(action=action).inc()


# Singleton instance
metrics_service = MetricsService()
