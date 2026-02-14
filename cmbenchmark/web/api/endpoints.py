"""API endpoints for cmbenchmark web interface."""

import json
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from cmbenchmark.services.scan import scan_dataset
from cmbenchmark.services.parse import parse_from_scan
from cmbenchmark.services.measure import compute_measure, save_measure_dataset, save_measure_per_model
from cmbenchmark.services.report import generate_report
from cmbenchmark.parser import get_all_parsers
from cmbenchmark.types.ir import IR
from cmbenchmark.types.dataset import IRInfo
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.construct_catalog import load_construct_profile_json, get_construct_profile_path
from .schemas import (
    ScanRequest, ScanResponse, ParseRequest, ParseResponse, ErrorResponse,
    MeasureRequest, MeasureResponse, ReportRequest, DerivedReportResponse
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


@router.post("/scan", response_model=ScanResponse)
async def scan(request: ScanRequest):
    """
    Scan a dataset directory for model files and generate statistics.
    
    This endpoint wraps the scan_dataset service function.
    The dataset_info.json file is saved to the profile's output_path.
    """
    try:
        profile = _normalize_profile(request.profile)
        dataset_info = scan_dataset(
            dataset_path=profile.scan.dataset_path,
            include=profile.scan.include,
            exclude=profile.scan.exclude,
            size_limit_mb=profile.scan.size_limit_mb,
        )
        
        # Save dataset_info.json to the output directory
        output_dir = Path(profile.output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset_info_path = output_dir / "dataset_info.json"
        with open(dataset_info_path, "w", encoding="utf-8") as f:
            json.dump(dataset_info.to_dict(), f, indent=2)
        
        # Convert DatasetInfo to response schema
        response = ScanResponse(
            dataset_root=dataset_info.dataset_root,
            scanned_at=dataset_info.scanned_at,
            parameters=dataset_info.parameters,
            totals=dataset_info.totals,
            extensions=dataset_info.extensions,
            duplicates_groups=dataset_info.duplicates_groups,
            too_large=dataset_info.too_large,
            unreadable=dataset_info.unreadable,
            candidates=dataset_info.candidates,
            filtered=dataset_info.filtered,
        )
        
        # Add the saved path and output directory to parameters for convenience
        response.parameters["dataset_info_path"] = str(dataset_info_path)
        response.parameters["out"] = str(output_dir)
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/parse", response_model=ParseResponse)
async def parse(request: ParseRequest):
    """
    Parse models from dataset_info.json and produce IR files.
    
    This endpoint wraps the parse_from_scan service function.
    """
    try:
        profile = _normalize_profile(request.profile)
        dataset_info_path = Path(profile.output_path).resolve() / "dataset_info.json"
        ir_info = parse_from_scan(
            dataset_info_path=str(dataset_info_path),
            output_dir=profile.output_path,
            parser_language=profile.parse.parser_language,
            ecore_enable_scoped_uri_mappings=getattr(
                profile.parse, "ecore_enable_scoped_uri_mappings", None
            ),
        )
        
        # Convert ModelParseDiagnostics to response schema
        diagnostics = {
            k: v.to_dict() if hasattr(v, 'to_dict') else v
            for k, v in ir_info.modelParseDiagnostics.items()
        }
        
        # Convert IRInfo to response schema
        response = ParseResponse(
            dataset_root=ir_info.dataset_root,
            parsed_at=ir_info.parsed_at,
            parameters=ir_info.parameters,
            totals=ir_info.totals,
            index=ir_info.index,
            modelParseDiagnostics=diagnostics,
        )
        # Add output_dir to parameters for convenience
        response.parameters["output_dir"] = profile.output_path
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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


@router.post("/measure", response_model=MeasureResponse)
async def measure(request: MeasureRequest):
    """
    Compute dataset-level and per-model measures from IR models.
    
    This endpoint wraps the compute_measure service function.
    The measures.json and measures_per_model.json files are saved to the profile's output_path.
    """
    try:
        profile = _normalize_profile(request.profile)
        ir_dir = Path(profile.output_path).resolve() / "ir"

        # Compute measures
        dataset_measures, per_model_measures = compute_measure(str(ir_dir), profile=profile)
        
        # Save measures to output directory
        output_dir = Path(profile.output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        measures_path = output_dir / "measures.json"
        measures_per_model_path = output_dir / "measures_per_model.json"
        
        save_measure_dataset(dataset_measures, str(measures_path))
        save_measure_per_model(per_model_measures, str(measures_per_model_path))
        
        return MeasureResponse(
            measures_path=str(measures_path),
            measures_per_model_path=str(measures_per_model_path),
            output_dir=str(output_dir),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/report", response_model=DerivedReportResponse)
async def report(request: ReportRequest):
    """
    Build UI-ready derived report JSON from measures and IR info.
    
    This endpoint loads the measures JSON files, optionally IR info, and returns a stable
    derived payload that the frontend can render directly (charts, tables, etc.).
    """
    try:
        profile = _normalize_profile(request.profile)
        output_dir = Path(profile.output_path).resolve()
        
        measures_path = output_dir / "measures.json"
        if not measures_path.exists():
            raise HTTPException(status_code=404, detail=f"Measures file not found: {measures_path}")

        measures_per_model_path = output_dir / "measures_per_model.json"
        if not measures_per_model_path.exists():
            raise HTTPException(status_code=404, detail=f"Measures per model file not found: {measures_per_model_path}")

        ir_info_path = output_dir / "ir_info.json"

        report_result = generate_report(
            measures_path=str(measures_path),
            measures_per_model_path=str(measures_per_model_path),
            output_dir=str(output_dir),
            ir_info_path=str(ir_info_path) if ir_info_path.exists() else None,
        )
        return report_result["data"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
