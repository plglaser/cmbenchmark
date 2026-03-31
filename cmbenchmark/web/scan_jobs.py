"""Scan job orchestration for async REST endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from cmbenchmark.services.scan import scan_dataset, ScanCancelledError
from cmbenchmark.types.profile import BenchmarkProfile
from .jobs import BackgroundJobManager, JobCancelledError

SCAN_JOB_TYPE = "scan"
SCAN_FILE_CATEGORIES = {
    "candidates",
    "filtered",
    "unreadable",
    "too_large",
    "duplicates",
}
SCAN_FILES_DEFAULT_LIMIT = 100
SCAN_FILES_MAX_LIMIT = 2000
ScanFileCategory = Literal["candidates", "filtered", "unreadable", "too_large", "duplicates"]

scan_job_manager = BackgroundJobManager(max_workers=2)


def _scan_runner(
    job_id: str,
    payload: Dict[str, Any],
    manager: BackgroundJobManager,
) -> Dict[str, Any]:
    profile = BenchmarkProfile(**payload["profile"])
    output_dir = Path(profile.output_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    def _on_progress(update: Dict[str, Any]) -> None:
        manager.set_progress(job_id, update)

    try:
        dataset_info = scan_dataset(
            dataset_path=profile.scan.dataset_path,
            include=profile.scan.include,
            exclude=profile.scan.exclude,
            size_limit_mb=profile.scan.size_limit_mb,
            progress_callback=_on_progress,
            cancel_requested=lambda: manager.is_cancel_requested(job_id),
        )
    except ScanCancelledError as exc:
        raise JobCancelledError(str(exc)) from exc

    dataset_info_path = output_dir / "dataset_info.json"
    with open(dataset_info_path, "w", encoding="utf-8") as f:
        json.dump(dataset_info.to_dict(), f, indent=2)

    return {
        "dataset_root": dataset_info.dataset_root,
        "scanned_at": dataset_info.scanned_at,
        "parameters": {
            **dataset_info.parameters,
            "dataset_info_path": str(dataset_info_path),
            "out": str(output_dir),
        },
        "totals": dataset_info.totals,
        "extensions": dataset_info.extensions,
        "duplicates_groups_count": len(dataset_info.duplicates_groups),
        "duplicates_files_count": sum(
            int(group.get("count", 0)) for group in dataset_info.duplicates_groups
        ),
    }


def create_scan_job(profile: BenchmarkProfile) -> Dict[str, Any]:
    """Create async scan job and enqueue it."""
    return scan_job_manager.create_job(
        job_type=SCAN_JOB_TYPE,
        payload={"profile": profile.model_dump(mode="python")},
        runner=_scan_runner,
        initial_progress={
            "phase": "queued",
            "message": "Job queued.",
            "percentage": 0.0,
            "counters": {
                "total_files": 0,
                "files_processed": 0,
                "total_seen": 0,
                "filtered": 0,
                "candidate_total": 0,
                "candidates_processed": 0,
                "unreadable": 0,
                "too_large": 0,
                "duplicates_groups": 0,
            },
        },
    )


def get_scan_job(job_id: str) -> Dict[str, Any]:
    """Get scan job status snapshot."""
    job = scan_job_manager.get_job(job_id)
    if job["job_type"] != SCAN_JOB_TYPE:
        raise KeyError(f"Scan job not found: {job_id}")
    return job


def cancel_scan_job(job_id: str) -> bool:
    """Request cancellation for scan job."""
    return scan_job_manager.request_cancel(job_id)


def _load_dataset_info_for_job(job_id: str) -> Dict[str, Any]:
    job = get_scan_job(job_id)
    if job["status"] != "completed":
        raise RuntimeError("Scan job is not completed yet.")
    result = job.get("result") or {}
    dataset_info_path = result.get("parameters", {}).get("dataset_info_path")
    if not dataset_info_path:
        raise RuntimeError("dataset_info.json path missing from job result.")
    path = Path(dataset_info_path)
    if not path.exists():
        raise FileNotFoundError(f"dataset_info.json not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_scan_job_files(
    job_id: str,
    category: ScanFileCategory,
    offset: int = 0,
    limit: int = SCAN_FILES_DEFAULT_LIMIT,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Return paginated scan file details for a completed job."""
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if limit < 1 or limit > SCAN_FILES_MAX_LIMIT:
        raise ValueError(f"limit must be in range [1, {SCAN_FILES_MAX_LIMIT}]")
    if category not in SCAN_FILE_CATEGORIES:
        raise ValueError(f"Unsupported category: {category}")

    data = _load_dataset_info_for_job(job_id)
    q = (query or "").lower()

    if category == "duplicates":
        groups: List[Dict[str, Any]] = data.get("duplicates_groups", [])
        if q:
            groups = [
                group for group in groups
                if any(q in str(member).lower() for member in group.get("members", []))
            ]
        total = len(groups)
        items = groups[offset:offset + limit]
    else:
        if category not in data:
            raise ValueError(f"Category not found in dataset info: {category}")
        files = data.get(category, [])
        if q:
            files = [entry for entry in files if q in str(entry).lower()]
        total = len(files)
        items = files[offset:offset + limit]

    return {
        "job_id": job_id,
        "category": category,
        "offset": offset,
        "limit": limit,
        "total": total,
        "items": items,
    }


def clear_scan_jobs() -> None:
    """Clear all scan jobs (test helper)."""
    scan_job_manager.clear()
