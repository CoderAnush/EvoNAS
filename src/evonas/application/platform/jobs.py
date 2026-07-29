"""In-memory background job manager (Phase 9)."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Lifecycle of a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobRecord:
    """Serializable job snapshot."""

    id: str
    kind: str
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    result: Any = None
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "meta": self.meta,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


ProgressCallback = Callable[[float, str], None]
JobFn = Callable[[ProgressCallback], Any]
EventPublisher = Callable[[dict[str, Any]], None]


class JobManager:
    """Thread-pool job queue with progress + cancel flags."""

    def __init__(
        self,
        *,
        max_workers: int = 2,
        publish: EventPublisher | None = None,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers))
        self._jobs: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.RLock()
        self._publish = publish or (lambda _e: None)

    def submit(
        self,
        kind: str,
        fn: JobFn,
        *,
        meta: dict[str, Any] | None = None,
    ) -> JobRecord:
        """Queue a job and return its record."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        record = JobRecord(id=job_id, kind=kind, status=JobStatus.QUEUED, meta=meta or {})
        cancel = threading.Event()
        with self._lock:
            self._jobs[job_id] = record
            self._cancel_flags[job_id] = cancel

        def _progress(value: float, message: str = "") -> None:
            self.update(job_id, progress=max(0.0, min(1.0, value)), message=message)

        def _runner() -> Any:
            with self._lock:
                rec = self._jobs[job_id]
                if cancel.is_set():
                    rec.status = JobStatus.CANCELLED
                    rec.updated_at = time.time()
                    self._emit(rec)
                    return None
                rec.status = JobStatus.RUNNING
                rec.message = "started"
                rec.updated_at = time.time()
                self._emit(rec)
            try:
                result = fn(_progress)
                with self._lock:
                    rec = self._jobs[job_id]
                    if cancel.is_set():
                        rec.status = JobStatus.CANCELLED
                    else:
                        rec.status = JobStatus.COMPLETED
                        rec.progress = 1.0
                        rec.result = result
                        rec.message = "completed"
                    rec.updated_at = time.time()
                    self._emit(rec)
                return result
            except Exception as exc:  # noqa: BLE001
                logger.exception("Job %s failed", job_id)
                with self._lock:
                    rec = self._jobs[job_id]
                    rec.status = JobStatus.FAILED
                    rec.error = str(exc)
                    rec.message = "failed"
                    rec.updated_at = time.time()
                    self._emit(rec)
                raise

        future = self._executor.submit(_runner)
        with self._lock:
            self._futures[job_id] = future
        self._emit(record)
        return record

    def update(
        self,
        job_id: str,
        *,
        progress: float | None = None,
        message: str | None = None,
    ) -> JobRecord | None:
        """Update progress for a running job."""
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec is None:
                return None
            if progress is not None:
                rec.progress = progress
            if message is not None:
                rec.message = message
            rec.updated_at = time.time()
            snapshot = JobRecord(**{**rec.__dict__})
        self._emit(snapshot)
        return snapshot

    def cancel(self, job_id: str) -> JobRecord | None:
        """Request cancellation (cooperative for running jobs)."""
        with self._lock:
            rec = self._jobs.get(job_id)
            flag = self._cancel_flags.get(job_id)
            if rec is None:
                return None
            if flag is not None:
                flag.set()
            if rec.status == JobStatus.QUEUED:
                rec.status = JobStatus.CANCELLED
                rec.message = "cancelled"
                rec.updated_at = time.time()
            future = self._futures.get(job_id)
            if future is not None and not future.done():
                future.cancel()
            self._emit(rec)
            return JobRecord(**{**rec.__dict__})

    def get(self, job_id: str) -> JobRecord | None:
        """Fetch a job by id."""
        with self._lock:
            rec = self._jobs.get(job_id)
            return JobRecord(**{**rec.__dict__}) if rec else None

    def list_jobs(self, *, kind: str | None = None, limit: int = 100) -> list[JobRecord]:
        """List recent jobs (newest first)."""
        with self._lock:
            items = list(self._jobs.values())
        if kind:
            items = [j for j in items if j.kind == kind]
        items.sort(key=lambda j: j.created_at, reverse=True)
        return [JobRecord(**{**j.__dict__}) for j in items[:limit]]

    def queue_depth(self) -> dict[str, int]:
        """Counts by status."""
        with self._lock:
            counts = {s.value: 0 for s in JobStatus}
            for job in self._jobs.values():
                counts[job.status.value] = counts.get(job.status.value, 0) + 1
            return counts

    def shutdown(self, *, wait: bool = False) -> None:
        """Stop the executor."""
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _emit(self, record: JobRecord) -> None:
        try:
            self._publish({"type": "job", "job": record.to_dict()})
        except Exception:  # noqa: BLE001
            logger.debug("Job event publish failed", exc_info=True)
