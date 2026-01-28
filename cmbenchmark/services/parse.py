"""Parse service for converting models to IR."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from cmbenchmark.types.models import DatasetInfo, IRInfo, ParseFailure
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
    2. Parse: For each candidate file, attempt to parse it (any exceptions are tracked as failed_parse)
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
        "parsed_ok": 0,
        "failed_parse": 0,
    }

    failures: List[ParseFailure] = []
    index: Dict[str, str] = {}  # ir_id -> relpath

    # Stage 2: Process each candidate file
    for relpath in dataset_info.candidates:
        file_path = dataset_root / relpath
        if not file_path.exists():
            continue

        file_id = _compute_file_id(file_path)

        # Stage 2a: Parse
        try:
            ir = parser.parse(str(file_path))
            ir.id = file_id
        except Exception as e:
            totals["failed_parse"] += 1
            failures.append(ParseFailure(
                relpath=relpath,
                ir_id=None,
                error_class=type(e).__name__,
                message=str(e),
                parser=parser.parser_id,
            ))
            continue

        # Stage 2b: Add metadata to IR
        ir.data["source_path"] = str(file_path)
        ir.data["source_relpath"] = relpath
        try:
            ir.data["filesize"] = file_path.stat().st_size
        except Exception:
            pass

        # Stage 2c: Save IR file
        ir_filename = f"{ir.id}.json"
        ir_path = ir_dir / ir_filename
        ir.save(str(ir_path))

        # Update index and statistics
        index[ir.id] = relpath
        totals["parsed_ok"] += 1

    # Stage 3: Build IRInfo object
    ir_info = IRInfo(
        dataset_root=str(dataset_root),
        parsed_at=parsed_at,
        parameters={
            "from_scan": str(dataset_info_path),
            "parser_language": parser_language,
        },
        totals=totals,
        failures=failures,
        index=index,
    )

    # Stage 4: Save output files
    ir_info_path = output_path / "ir_info.json"
    with open(ir_info_path, "w", encoding="utf-8") as f:
        json.dump(ir_info.to_dict(), f, indent=2)

    return ir_info

