"""Generic background job manager for web API endpoints."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Dict, Optional
from uuid import uuid4


JobRunner = Callable[[str, Dict[str, Any], "BackgroundJobManager"], Dict[str, Any]]
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class JobCancelledError(Exception):
    """Raised by job runners when cancellation has been requested."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class JobRecord:
    """Internal mutable job record."""

    job_id: str
    job_type: str
    payload: Dict[str, Any]
    runner: JobRunner
    status: str = "queued"
    progress: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cancel_requested: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def snapshot(self) -> Dict[str, Any]:
        """Return a stable dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": deepcopy(self.progress),
            "result": deepcopy(self.result),
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cancel_requested": self.cancel_requested,
        }


class BackgroundJobManager:
    """Thread-safe in-memory background job manager."""

    def __init__(self, max_workers: int = 2):
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="cmbenchmark-job",
        )

    def create_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        runner: JobRunner,
        initial_progress: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create and enqueue a background job."""
        job_id = uuid4().hex
        record = JobRecord(
            job_id=job_id,
            job_type=job_type,
            payload=deepcopy(payload),
            runner=runner,
            progress=deepcopy(initial_progress or {}),
        )
        with self._lock:
            self._jobs[job_id] = record
        self._executor.submit(self._run_job, job_id)
        return record.snapshot()

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Return job snapshot."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(f"Job not found: {job_id}")
            return record.snapshot()

    def is_cancel_requested(self, job_id: str) -> bool:
        """Check whether cancellation was requested for job."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return False
            return record.cancel_requested

    def request_cancel(self, job_id: str) -> bool:
        """
        Request cancellation.

        Returns True when a new cancellation request was accepted, False when the
        job is already in a terminal status.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(f"Job not found: {job_id}")

            if record.status in TERMINAL_STATUSES:
                return False

            record.cancel_requested = True
            if record.status == "queued":
                record.status = "cancelled"
                record.finished_at = _utc_now_iso()
            elif record.status == "running":
                record.status = "cancel_requested"
            return True

    def set_progress(self, job_id: str, progress: Dict[str, Any]) -> None:
        """Update in-flight progress metadata."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            if record.status in TERMINAL_STATUSES:
                return
            record.progress = deepcopy(progress)

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """Mark a job as completed."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            if record.status in TERMINAL_STATUSES:
                return
            record.status = "completed"
            record.result = deepcopy(result)
            record.finished_at = _utc_now_iso()

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            if record.status in TERMINAL_STATUSES:
                return
            record.status = "failed"
            record.error = error
            record.finished_at = _utc_now_iso()

    def cancel_job(self, job_id: str) -> None:
        """Mark a running job as cancelled."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            if record.status in TERMINAL_STATUSES:
                return
            record.status = "cancelled"
            record.finished_at = _utc_now_iso()

    def clear(self) -> None:
        """Clear all jobs. Intended for tests."""
        with self._lock:
            self._jobs.clear()

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            if record.status != "queued":
                return
            if record.cancel_requested:
                record.status = "cancelled"
                record.finished_at = _utc_now_iso()
                return
            record.status = "running"
            record.started_at = _utc_now_iso()
            runner = record.runner
            payload = deepcopy(record.payload)

        try:
            result = runner(job_id, payload, self)
        except JobCancelledError:
            self.cancel_job(job_id)
            return
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.fail_job(job_id, str(exc))
            return

        if self.is_cancel_requested(job_id):
            self.cancel_job(job_id)
            return
        self.complete_job(job_id, result)
