"""API endpoints for cmbenchmark web interface."""

import json
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from cmbenchmark.services.scan import scan_dataset
from cmbenchmark.services.parse import parse_from_scan
from cmbenchmark.parser import get_all_parsers
from cmbenchmark.types.ir import IR
from .schemas import ScanRequest, ScanResponse, ParseRequest, ParseResponse, ParseFailureResponse, ErrorResponse

router = APIRouter()


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
    The dataset_info.json file is saved to the output directory specified in 'out'.
    """
    try:
        dataset_info = scan_dataset(
            dataset_path=request.dataset_path,
            include=request.include,
            exclude=request.exclude,
            size_limit_mb=request.size_limit_mb,
        )
        
        # Save dataset_info.json to the output directory
        output_dir = Path(request.out).resolve()
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
        ir_info, loss_report = parse_from_scan(
            dataset_info_path=request.dataset_info_path,
            output_dir=request.output_dir,
            parser_language=request.parser_language,
        )
        
        # Convert ParseFailure objects to response schema
        failures = [
            ParseFailureResponse(
                relpath=f.relpath,
                ir_id=f.ir_id,
                stage=f.stage,
                error_class=f.error_class,
                message=f.message,
                parser=f.parser,
            )
            for f in ir_info.failures
        ]
        
        # Convert IRInfo to response schema
        return ParseResponse(
            dataset_root=ir_info.dataset_root,
            parsed_at=ir_info.parsed_at,
            parameters=ir_info.parameters,
            totals=ir_info.totals,
            loss_summary=ir_info.loss_summary,
            failures=failures,
            index=ir_info.index,
        )
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

