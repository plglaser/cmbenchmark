"""API endpoints for cmbenchmark web interface."""

from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from cmbenchmark.parser import get_all_parsers
from cmbenchmark.types.ir import IR
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.construct_catalog import load_construct_profile_json, get_construct_profile_path
from cmbenchmark.web.scan_jobs import (
    create_scan_job,
    get_scan_job,
    get_scan_job_files,
    cancel_scan_job,
    SCAN_FILES_DEFAULT_LIMIT,
    SCAN_FILES_MAX_LIMIT,
    ScanFileCategory,
)
from cmbenchmark.web.parse_jobs import create_parse_job, get_parse_job, cancel_parse_job
from cmbenchmark.web.measure_jobs import create_measure_job, get_measure_job, cancel_measure_job
from cmbenchmark.web.report_jobs import create_report_job, get_report_job, cancel_report_job
from .schemas import (
    ScanRequest,
    ScanJobCreateResponse,
    ScanJobStatusResponse,
    ScanJobFilesResponse,
    ScanJobCancelResponse,
    StageJobCreateResponse,
    StageJobStatusResponse,
    StageJobCancelResponse,
    ParseRequest,
    MeasureRequest,
    ReportRequest,
)

router = APIRouter()


def _normalize_profile(profile: BenchmarkProfile) -> BenchmarkProfile:
    """Normalize inline profile data (absolute paths)."""
    if profile.scan and profile.scan.dataset_path:
        dataset_path = Path(profile.scan.dataset_path).expanduser()
        profile.scan.dataset_path = str(dataset_path.resolve())

    if profile.output_path:
        output_path = Path(profile.output_path).expanduser()
        profile.output_path = str(output_path.resolve())

    return profile

@router.get("/construct-profile", response_model=Dict[str, Any])
async def get_construct_profile(
    parser_language: str = Query(..., description="Parser language (e.g., ArchiMate-Archi, ArchiMate-XML, Ecore)"),
):
    """
    Return the construct profile JSON for a given parser language.

    This serves the packaged JSON files in `cmbenchmark/measures/construct_profiles/`.
    Intended for UI introspection (e.g. showing the catalog of constructs + match rules).
    """
    try:
        # Be forgiving: allow passing the language name ("ArchiMate"/"Ecore") as well.
        normalized = parser_language
        if parser_language == "ArchiMate":
            normalized = "ArchiMate-Archi"

        profile_path = get_construct_profile_path(normalized)
        if not profile_path:
            raise HTTPException(status_code=404, detail=f"No construct profile found for parser_language={parser_language}")

        data = load_construct_profile_json(normalized)
        if not data:
            raise HTTPException(status_code=404, detail=f"Construct profile file not found: {profile_path}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/parsers", response_model=List[str])
async def get_parsers():
    """Get list of available parser languages."""
    parsers = get_all_parsers()
    return [parser.language for parser in parsers]


@router.post("/scan-jobs", response_model=ScanJobCreateResponse, status_code=202)
async def start_scan_job(request: ScanRequest):
    """Create an asynchronous scan job and return a job id."""
    try:
        profile = _normalize_profile(request.profile)
        job = create_scan_job(profile)
        return ScanJobCreateResponse(
            job_id=job["job_id"],
            status=job["status"],
            created_at=job["created_at"],
            status_url=f"/api/scan-jobs/{job['job_id']}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scan-jobs/{job_id}", response_model=ScanJobStatusResponse)
async def scan_job_status(job_id: str):
    """Get current status/progress for a scan job."""
    try:
        job = get_scan_job(job_id)
        return ScanJobStatusResponse(**job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scan job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scan-jobs/{job_id}/files", response_model=ScanJobFilesResponse)
async def scan_job_files(
    job_id: str,
    category: ScanFileCategory = Query(
        ...,
        description="One of: candidates, filtered, unreadable, too_large, duplicates",
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(SCAN_FILES_DEFAULT_LIMIT, ge=1, le=SCAN_FILES_MAX_LIMIT),
    q: str = Query("", description="Case-insensitive substring filter"),
):
    """Get paginated scan details for a completed scan job."""
    try:
        data = get_scan_job_files(
            job_id=job_id,
            category=category,
            offset=offset,
            limit=limit,
            query=q,
        )
        return ScanJobFilesResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scan job not found: {job_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/scan-jobs/{job_id}", response_model=ScanJobCancelResponse)
async def cancel_scan(job_id: str):
    """Request cancellation of a scan job."""
    try:
        cancel_requested = cancel_scan_job(job_id)
        job = get_scan_job(job_id)
        return ScanJobCancelResponse(
            job_id=job_id,
            status=job["status"],
            cancel_requested=cancel_requested,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scan job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/parse-jobs", response_model=StageJobCreateResponse, status_code=202)
async def start_parse_job(request: ParseRequest):
    """Create an asynchronous parse job and return a job id."""
    try:
        profile = _normalize_profile(request.profile)
        job = create_parse_job(profile)
        return StageJobCreateResponse(
            job_id=job["job_id"],
            status=job["status"],
            created_at=job["created_at"],
            status_url=f"/api/parse-jobs/{job['job_id']}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/parse-jobs/{job_id}", response_model=StageJobStatusResponse)
async def parse_job_status(job_id: str):
    """Get current status for a parse job."""
    try:
        job = get_parse_job(job_id)
        return StageJobStatusResponse(**job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Parse job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/parse-jobs/{job_id}", response_model=StageJobCancelResponse)
async def cancel_parse(job_id: str):
    """Request cancellation of a parse job."""
    try:
        cancel_requested = cancel_parse_job(job_id)
        job = get_parse_job(job_id)
        return StageJobCancelResponse(
            job_id=job_id,
            status=job["status"],
            cancel_requested=cancel_requested,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Parse job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/measure-jobs", response_model=StageJobCreateResponse, status_code=202)
async def start_measure_job(request: MeasureRequest):
    """Create an asynchronous measure job and return a job id."""
    try:
        profile = _normalize_profile(request.profile)
        job = create_measure_job(profile)
        return StageJobCreateResponse(
            job_id=job["job_id"],
            status=job["status"],
            created_at=job["created_at"],
            status_url=f"/api/measure-jobs/{job['job_id']}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/measure-jobs/{job_id}", response_model=StageJobStatusResponse)
async def measure_job_status(job_id: str):
    """Get current status for a measure job."""
    try:
        job = get_measure_job(job_id)
        return StageJobStatusResponse(**job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Measure job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/measure-jobs/{job_id}", response_model=StageJobCancelResponse)
async def cancel_measure(job_id: str):
    """Request cancellation of a measure job."""
    try:
        cancel_requested = cancel_measure_job(job_id)
        job = get_measure_job(job_id)
        return StageJobCancelResponse(
            job_id=job_id,
            status=job["status"],
            cancel_requested=cancel_requested,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Measure job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/report-jobs", response_model=StageJobCreateResponse, status_code=202)
async def start_report_job(request: ReportRequest):
    """Create an asynchronous report job and return a job id."""
    try:
        profile = _normalize_profile(request.profile)
        job = create_report_job(profile)
        return StageJobCreateResponse(
            job_id=job["job_id"],
            status=job["status"],
            created_at=job["created_at"],
            status_url=f"/api/report-jobs/{job['job_id']}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/report-jobs/{job_id}", response_model=StageJobStatusResponse)
async def report_job_status(job_id: str):
    """Get current status for a report job."""
    try:
        job = get_report_job(job_id)
        return StageJobStatusResponse(**job)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Report job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/report-jobs/{job_id}", response_model=StageJobCancelResponse)
async def cancel_report(job_id: str):
    """Request cancellation of a report job."""
    try:
        cancel_requested = cancel_report_job(job_id)
        job = get_report_job(job_id)
        return StageJobCancelResponse(
            job_id=job_id,
            status=job["status"],
            cancel_requested=cancel_requested,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Report job not found: {job_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/ir/{ir_id}")
async def get_ir(ir_id: str, output_dir: str = Query(..., description="Output directory where IR files are stored")):
    """
    Get IR file by ID.
    
    Args:
        ir_id: The IR file ID (filename without .json extension)
        output_dir: The output directory where IR files are stored
    """
    try:
        output_path = Path(output_dir).resolve()
        ir_path = output_path / "ir" / f"{ir_id}.json"
        
        if not ir_path.exists():
            raise HTTPException(status_code=404, detail=f"IR file not found: {ir_id}")
        
        ir = IR.load(str(ir_path))
        return ir.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
