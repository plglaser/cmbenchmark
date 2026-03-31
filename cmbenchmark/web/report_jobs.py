"""Report job orchestration for async REST endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from cmbenchmark.services.report import generate_report, ReportCancelledError
from cmbenchmark.types.profile import BenchmarkProfile
from .jobs import BackgroundJobManager, JobCancelledError

REPORT_JOB_TYPE = "report"

report_job_manager = BackgroundJobManager(max_workers=1)


def _report_runner(
    job_id: str,
    payload: Dict[str, Any],
    manager: BackgroundJobManager,
) -> Dict[str, Any]:
    profile = BenchmarkProfile(**payload["profile"])
    output_dir = Path(profile.output_path).resolve()
    measures_path = output_dir / "measures.json"
    measures_index_path = output_dir / "measures_index.json"
    ir_info_path = output_dir / "ir_info.json"

    manager.set_progress(
        job_id,
        {
            "phase": "running",
            "message": "Starting report stage.",
            "percentage": 0.0,
        },
    )

    try:
        report_result = generate_report(
            measures_path=str(measures_path),
            measures_index_path=str(measures_index_path),
            output_dir=str(output_dir),
            ir_info_path=str(ir_info_path) if ir_info_path.exists() else None,
            progress_callback=lambda update: manager.set_progress(job_id, update),
            cancel_requested=lambda: manager.is_cancel_requested(job_id),
        )
    except ReportCancelledError as exc:
        raise JobCancelledError(str(exc)) from exc
    return report_result["data"]


def create_report_job(profile: BenchmarkProfile) -> Dict[str, Any]:
    """Create async report job and enqueue it."""
    return report_job_manager.create_job(
        job_type=REPORT_JOB_TYPE,
        payload={"profile": profile.model_dump(mode="python")},
        runner=_report_runner,
        initial_progress={
            "phase": "queued",
            "message": "Job queued.",
            "percentage": 0.0,
            "counters": {
                "total_models": 0,
                "processed_models": 0,
            },
        },
    )


def get_report_job(job_id: str) -> Dict[str, Any]:
    """Get report job status snapshot."""
    job = report_job_manager.get_job(job_id)
    if job["job_type"] != REPORT_JOB_TYPE:
        raise KeyError(f"Report job not found: {job_id}")
    return job


def cancel_report_job(job_id: str) -> bool:
    """Request cancellation for report job."""
    return report_job_manager.request_cancel(job_id)


def clear_report_jobs() -> None:
    """Clear all report jobs (test helper)."""
    report_job_manager.clear()
