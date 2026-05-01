"""
Worker client for PiGenus.
This is a reference implementation for workers to communicate with PiGenus.
"""
import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkerConfig(BaseModel):
    """Configuration for a PiGenus worker."""
    name: str
    pigenus_url: str = "http://localhost:8000"
    api_token: str
    capabilities: Dict[str, Any] = {}
    heartbeat_interval: int = 30  # seconds
    poll_interval: int = 5  # seconds


class WorkerClient:
    """
    Client for a worker to communicate with PiGenus.
    Handles registration, heartbeat, and job processing.
    """

    def __init__(self, config: WorkerConfig):
        self.config = config
        self.worker_id: Optional[int] = None
        self.client = httpx.Client(
            base_url=config.pigenus_url,
            headers={"Authorization": f"Bearer {config.api_token}"}
        )

    def register(self) -> bool:
        """
        Register the worker with PiGenus.
        Returns True if successful.
        """
        try:
            response = self.client.post(
                "/workers/register",
                json={
                    "name": self.config.name,
                    "capabilities": self.config.capabilities
                }
            )
            response.raise_for_status()
            data = response.json()
            self.worker_id = data["id"]
            logger.info(f"Worker registered with ID: {self.worker_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register worker: {e}")
            return False

    def heartbeat(self) -> bool:
        """
        Send a heartbeat to PiGenus.
        Returns True if successful.
        """
        if not self.worker_id:
            logger.warning("Worker not registered, cannot send heartbeat")
            return False

        try:
            response = self.client.post(
                "/workers/heartbeat",
                json={"worker_id": self.worker_id}
            )
            response.raise_for_status()
            logger.debug(f"Heartbeat sent for worker {self.worker_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    def lease_job(self) -> Optional[Dict[str, Any]]:
        """
        Lease a job from PiGenus.
        Returns the job data or None if no jobs available.
        """
        if not self.worker_id:
            logger.warning("Worker not registered, cannot lease job")
            return None

        try:
            response = self.client.get(
                f"/jobs/lease?worker_id={self.worker_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data is None:
                return None
            return data
        except Exception as e:
            logger.error(f"Failed to lease job: {e}")
            return None

    def acknowledge_job(self, job_id: int, result: Dict[str, Any]) -> bool:
        """
        Acknowledge successful completion of a job.
        Returns True if successful.
        """
        try:
            response = self.client.post(
                f"/jobs/{job_id}/ack",
                json={"result": result}
            )
            response.raise_for_status()
            logger.info(f"Job {job_id} acknowledged")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge job {job_id}: {e}")
            return False

    def fail_job(self, job_id: int, error: str) -> bool:
        """
        Report failure of a job.
        Returns True if successful.
        """
        try:
            response = self.client.post(
                f"/jobs/{job_id}/fail",
                json={"error": error}
            )
            response.raise_for_status()
            logger.warning(f"Job {job_id} failed: {error}")
            return True
        except Exception as e:
            logger.error(f"Failed to report job failure {job_id}: {e}")
            return False

    def process_job(self, job: Dict[str, Any]) -> bool:
        """
        Process a leased job.
        This is a placeholder - override this method in subclasses.
        """
        logger.info(f"Processing job: {job}")
        # Simulate work
        time.sleep(1)
        return True

    def run(self):
        """
        Main worker loop.
        Handles registration, heartbeat, and job processing.
        """
        # Register the worker
        if not self.register():
            logger.error("Failed to register worker, exiting")
            return

        # Start heartbeat thread
        import threading
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        heartbeat_thread.start()

        # Main loop: lease and process jobs
        logger.info("Worker started, waiting for jobs...")
        while True:
            try:
                # Lease a job
                job_data = self.lease_job()
                if job_data:
                    job = job_data["job"]
                    lease_expires = job_data["lease_expires_at"]
                    
                    logger.info(f"Leased job {job['id']}, expires at {lease_expires}")
                    
                    # Process the job
                    try:
                        result = {"status": "completed", "timestamp": datetime.utcnow().isoformat()}
                        if self.process_job(job):
                            self.acknowledge_job(job["id"], result)
                        else:
                            self.fail_job(job["id"], "Processing failed")
                    except Exception as e:
                        self.fail_job(job["id"], str(e))
                else:
                    # No jobs available, wait before polling again
                    time.sleep(self.config.poll_interval)
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(self.config.poll_interval)

    def _heartbeat_loop(self):
        """Heartbeat loop running in background thread."""
        while True:
            try:
                self.heartbeat()
                time.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(self.config.heartbeat_interval)


class TestWorker(WorkerClient):
    """Test worker implementation for demonstration."""

    def process_job(self, job: Dict[str, Any]) -> bool:
        """Process a job by echoing the input."""
        logger.info(f"TestWorker processing job: {job}")
        task = job.get("task", {})
        
        # Simulate work
        time.sleep(0.5)
        
        # Return a result
        result = {
            "input": task,
            "output": f"Processed: {task}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"TestWorker result: {result}")
        return True


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    # Example usage
    config = WorkerConfig(
        name="test-worker",
        pigenus_url=os.getenv("PIGENUS_URL", "http://localhost:8000"),
        api_token=os.getenv("API_TOKEN", ""),
        capabilities={"test": True}
    )

    worker = TestWorker(config)
    worker.run()
