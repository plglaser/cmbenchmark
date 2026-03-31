"""Parse job orchestration for async REST endpoints."""

from __future__ import annotations

from typing import Any, Dict
from pathlib import Path

from cmbenchmark.services.parse import parse_from_scan, ParseCancelledError
from cmbenchmark.types.profile import BenchmarkProfile
from .jobs import BackgroundJobManager, JobCancelledError

PARSE_JOB_TYPE = "parse"

parse_job_manager = BackgroundJobManager(max_workers=1)


def _parse_runner(
    job_id: str,
    payload: Dict[str, Any],
    manager: BackgroundJobManager,
) -> Dict[str, Any]:
    profile = BenchmarkProfile(**payload["profile"])
    output_dir = Path(profile.output_path).resolve()
    dataset_info_path = output_dir / "dataset_info.json"

    manager.set_progress(
        job_id,
        {
            "phase": "running",
            "message": "Starting parse stage.",
            "percentage": 0.0,
        },
    )

    try:
        ir_info = parse_from_scan(
            dataset_info_path=str(dataset_info_path),
            output_dir=str(output_dir),
            parser_language=profile.parse.parser_language,
            ecore_enable_scoped_uri_mappings=getattr(
                profile.parse, "ecore_enable_scoped_uri_mappings", None
            ),
            progress_callback=lambda update: manager.set_progress(job_id, update),
            cancel_requested=lambda: manager.is_cancel_requested(job_id),
        )
    except ParseCancelledError as exc:
        raise JobCancelledError(str(exc)) from exc

    diagnostics = {
        k: v.to_dict() if hasattr(v, "to_dict") else v
        for k, v in ir_info.modelParseDiagnostics.items()
    }
    parameters = dict(ir_info.parameters)
    parameters["output_dir"] = str(output_dir)

    return {
        "dataset_root": ir_info.dataset_root,
        "parsed_at": ir_info.parsed_at,
        "parameters": parameters,
        "totals": ir_info.totals,
        "index": ir_info.index,
        "modelParseDiagnostics": diagnostics,
    }


def create_parse_job(profile: BenchmarkProfile) -> Dict[str, Any]:
    """Create async parse job and enqueue it."""
    return parse_job_manager.create_job(
        job_type=PARSE_JOB_TYPE,
        payload={"profile": profile.model_dump(mode="python")},
        runner=_parse_runner,
        initial_progress={
            "phase": "queued",
            "message": "Job queued.",
            "percentage": 0.0,
            "counters": {
                "total_models": 0,
                "processed_models": 0,
                "parsed_success": 0,
                "parsed_warning": 0,
                "parsed_failure": 0,
            },
        },
    )


def get_parse_job(job_id: str) -> Dict[str, Any]:
    """Get parse job status snapshot."""
    job = parse_job_manager.get_job(job_id)
    if job["job_type"] != PARSE_JOB_TYPE:
        raise KeyError(f"Parse job not found: {job_id}")
    return job


def cancel_parse_job(job_id: str) -> bool:
    """Request cancellation for parse job."""
    return parse_job_manager.request_cancel(job_id)


def clear_parse_jobs() -> None:
    """Clear all parse jobs (test helper)."""
    parse_job_manager.clear()
