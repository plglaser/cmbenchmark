"""Measure job orchestration for async REST endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from cmbenchmark.services.measure import (
    compute_measure,
    save_measure_dataset,
    save_measure_per_model_split,
    MeasureCancelledError,
)
from cmbenchmark.types.profile import BenchmarkProfile
from .jobs import BackgroundJobManager, JobCancelledError

MEASURE_JOB_TYPE = "measure"

measure_job_manager = BackgroundJobManager(max_workers=1)


def _measure_runner(
    job_id: str,
    payload: Dict[str, Any],
    manager: BackgroundJobManager,
) -> Dict[str, Any]:
    profile = BenchmarkProfile(**payload["profile"])
    output_dir = Path(profile.output_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ir_dir = output_dir / "ir"

    manager.set_progress(
        job_id,
        {
            "phase": "running",
            "message": "Starting measure stage.",
            "percentage": 0.0,
        },
    )

    try:
        dataset_measures, per_model_measures = compute_measure(
            str(ir_dir),
            profile=profile,
            progress_callback=lambda update: manager.set_progress(job_id, update),
            cancel_requested=lambda: manager.is_cancel_requested(job_id),
        )
    except MeasureCancelledError as exc:
        raise JobCancelledError(str(exc)) from exc

    manager.set_progress(
        job_id,
        {
            "phase": "writing_results",
            "message": "Writing measure artifacts to disk.",
            "percentage": 95.0,
            "counters": {
                "total_models": int(getattr(dataset_measures, "num_models", 0) or 0),
                "processed_models": int(getattr(dataset_measures, "num_models", 0) or 0),
                "valid_models_loaded": int(getattr(dataset_measures, "num_models", 0) or 0),
            },
        },
    )

    measures_path = output_dir / "measures.json"
    save_measure_dataset(dataset_measures, str(measures_path))
    save_measure_per_model_split(per_model_measures, str(output_dir))

    measures_dir = output_dir / "measures"
    measures_index_path = output_dir / "measures_index.json"

    return {
        "measures_path": str(measures_path),
        "measures_dir": str(measures_dir),
        "measures_index_path": str(measures_index_path),
        "output_dir": str(output_dir),
    }


def create_measure_job(profile: BenchmarkProfile) -> Dict[str, Any]:
    """Create async measure job and enqueue it."""
    return measure_job_manager.create_job(
        job_type=MEASURE_JOB_TYPE,
        payload={"profile": profile.model_dump(mode="python")},
        runner=_measure_runner,
        initial_progress={
            "phase": "queued",
            "message": "Job queued.",
            "percentage": 0.0,
            "counters": {
                "total_models": 0,
                "processed_models": 0,
                "valid_models_loaded": 0,
            },
        },
    )


def get_measure_job(job_id: str) -> Dict[str, Any]:
    """Get measure job status snapshot."""
    job = measure_job_manager.get_job(job_id)
    if job["job_type"] != MEASURE_JOB_TYPE:
        raise KeyError(f"Measure job not found: {job_id}")
    return job


def cancel_measure_job(job_id: str) -> bool:
    """Request cancellation for measure job."""
    return measure_job_manager.request_cancel(job_id)


def clear_measure_jobs() -> None:
    """Clear all measure jobs (test helper)."""
    measure_job_manager.clear()
