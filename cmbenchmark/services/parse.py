"""Parse service for converting models to IR."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from cmbenchmark.types.models import (
    DatasetInfo, IRInfo, ModelParseDiagnostics, 
    WarningType, ParseStatus
)
from cmbenchmark.parser import get_parser, get_all_parsers
from cmbenchmark.types.ir import IR


def _compute_file_id(file_path: Path) -> str:
    """Compute deterministic ID for a file using SHA256 hash."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]
    except Exception:
        # Fallback to filename-based ID if file can't be read
        return hashlib.sha256(str(file_path).encode()).hexdigest()[:16]


def _get_parser_by_language(parser_language: str):
    """
    Get parser class by language name with case-insensitive matching.
    
    Args:
        parser_language: Language name (e.g., "UML", "BPMN", "ArchiMate")
        
    Returns:
        Parser class or None if not found
    """
    # Try exact match first
    parser_class = get_parser(parser_language)
    if parser_class:
        return parser_class
    
    # Try case-insensitive match
    parser_language_lower = parser_language.lower()
    for parser_cls in get_all_parsers():
        if parser_cls.language.lower() == parser_language_lower:
            return parser_cls
    
    return None


def parse_from_scan(
    dataset_info_path: str,
    output_dir: str,
    parser_language: str,
) -> IRInfo:
    """
    Parse models from dataset_info.json and produce IR files.

    The parsing process follows these stages:
    1. Initialize: Load dataset info, setup parser, prepare output directories
    2. Parse: For each candidate file, attempt to parse it (status tracked as success/warning/failure)
    3. Save: Save IR files

    Args:
        dataset_info_path: Path to dataset_info.json from scan stage
        output_dir: Path to output directory
        parser_language: Language name of the parser to use (e.g., "UML", "BPMN", "ArchiMate")

    Returns:
        IRInfo object
    """
    # Stage 1: Initialize
    dataset_info_file = Path(dataset_info_path)
    if not dataset_info_file.exists():
        raise ValueError(f"Dataset info file does not exist: {dataset_info_path}")

    with open(dataset_info_file, "r", encoding="utf-8") as f:
        dataset_info_data = json.load(f)
    dataset_info = DatasetInfo.from_dict(dataset_info_data)

    dataset_root = Path(dataset_info.dataset_root)
    if not dataset_root.exists():
        raise ValueError(f"Dataset root does not exist: {dataset_root}")

    output_path = Path(output_dir)
    ir_dir = output_path / "ir"
    ir_dir.mkdir(parents=True, exist_ok=True)

    parser_class = _get_parser_by_language(parser_language)
    if not parser_class:
        raise ValueError(f"Parser not found for language: {parser_language}")

    parser = parser_class()
    parsed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Initialize tracking structures
    totals = {
        "candidates_in": len(dataset_info.candidates),
        "parsed_success": 0,
        "parsed_warning": 0,
        "parsed_failure": 0,
    }

    index: Dict[str, str] = {}  # ir_id -> relpath
    model_diagnostics: Dict[str, ModelParseDiagnostics] = {}  # ir_id -> diagnostics

    # Stage 2: Process each candidate file
    for relpath in dataset_info.candidates:
        file_path = dataset_root / relpath
        if not file_path.exists():
            continue

        file_id = _compute_file_id(file_path)
        
        # Initialize diagnostics
        diagnostics = ModelParseDiagnostics(
            file_id=file_id,
            relpath=relpath,
            parse_status="failure",  # Will be updated on success
        )
        
        # Get source file size
        try:
            diagnostics.file_size_bytes_source = file_path.stat().st_size
        except Exception:
            pass

        # Stage 2a: Parse with timing
        parser._start_run()
        parse_start_time = time.perf_counter()
        ir = None
        
        try:
            ir, run_stats = parser.parse(str(file_path))
            parse_end_time = time.perf_counter()
            parse_time_ms = int((parse_end_time - parse_start_time) * 1000)
            
            ir.id = file_id
            
            # Update diagnostics from successful parse
            diagnostics.parse_time_ms = parse_time_ms
            diagnostics.elements_loaded = len(ir.nodes) + len(ir.edges)
            diagnostics.elements_skipped = run_stats.elements_skipped
            diagnostics.warning_count = run_stats.warning_count
            diagnostics.warnings_by_type = {
                wt.value: count for wt, count in run_stats.warnings_by_type.items()
            }
            diagnostics.warning_msgs = {
                wt.value: msgs for wt, msgs in run_stats.warning_msgs.items()
            }
            
            # Determine parse status
            if diagnostics.warning_count == 0 and diagnostics.elements_skipped == 0:
                diagnostics.parse_status = "success"
            elif diagnostics.elements_loaded > 0:
                diagnostics.parse_status = "warning"
            else:
                diagnostics.parse_status = "failure"
                diagnostics.parse_error_msg = "No elements loaded"
            
        except Exception as e:
            parse_end_time = time.perf_counter()
            parse_time_ms = int((parse_end_time - parse_start_time) * 1000)
            
            diagnostics.parse_time_ms = parse_time_ms
            diagnostics.parse_status = "failure"
            diagnostics.parse_error_msg = f"{type(e).__name__}: {str(e)}"

        # Stage 2b: Save IR file if parsing succeeded
        if ir is not None:
            # Add metadata to IR
            ir.data["source_path"] = str(file_path)
            ir.data["source_relpath"] = relpath
            try:
                ir.data["filesize"] = file_path.stat().st_size
            except Exception:
                pass

            # Save IR file
            ir_filename = f"{ir.id}.json"
            ir_path = ir_dir / ir_filename
            ir.save(str(ir_path))
            
            # Get IR file size
            try:
                diagnostics.file_size_bytes_ir = ir_path.stat().st_size
            except Exception:
                pass

            # Update index
            index[ir.id] = relpath
            model_diagnostics[ir.id] = diagnostics
        else:
            # Store diagnostics for failures (using file_id since no IR was created)
            model_diagnostics[file_id] = diagnostics

        # Stage 2c: Update totals based on parse status
        if diagnostics.parse_status == "success":
            totals["parsed_success"] += 1
        elif diagnostics.parse_status == "warning":
            totals["parsed_warning"] += 1
        else:  # failure
            totals["parsed_failure"] += 1

    # Stage 3: Build IRInfo object
    ir_info = IRInfo(
        dataset_root=str(dataset_root),
        parsed_at=parsed_at,
        parameters={
            "from_scan": str(dataset_info_path),
            "parser_language": parser_language,
        },
        totals=totals,
        index=index,
        modelParseDiagnostics=model_diagnostics,
    )

    # Stage 4: Save output files
    ir_info_path = output_path / "ir_info.json"
    with open(ir_info_path, "w", encoding="utf-8") as f:
        json.dump(ir_info.to_dict(), f, indent=2)

    return ir_info

