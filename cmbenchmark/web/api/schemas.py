"""Pydantic schemas for API requests and responses."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from cmbenchmark.services.scan import DEFAULT_INCLUDE_PATTERNS


# Request schemas
class ScanRequest(BaseModel):
    """Request schema for scan endpoint."""
    dataset_path: str = Field(..., description="Path to dataset directory")
    out: str = Field(..., description="Path to output directory for dataset_info.json")
    include: Optional[List[str]] = Field(None, description=f"List of file patterns to include. If not provided, uses default patterns: {', '.join(DEFAULT_INCLUDE_PATTERNS)}. Patterns match filenames (e.g., '*.xml') or relative paths from dataset root (e.g., 'subdir/*').")
    exclude: Optional[List[str]] = Field(None, description="List of file patterns to exclude. Applied after include filtering. Patterns match filenames (e.g., '*.tmp') or relative paths from dataset root (e.g., 'test/*', 'backup/**').")
    size_limit_mb: Optional[int] = Field(None, description="Maximum file size in MB")


class ParseRequest(BaseModel):
    """Request schema for parse endpoint."""
    dataset_info_path: str = Field(..., description="Path to dataset_info.json from scan stage")
    output_dir: str = Field(..., description="Path to output directory")
    parser_language: str = Field(..., description="Parser language to use (e.g., UML, BPMN, ArchiMate)")


# Response schemas
class ScanResponse(BaseModel):
    """Response schema for scan endpoint."""
    dataset_root: str
    scanned_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    extensions: Dict[str, int]
    duplicates_groups: List[Dict[str, Any]]
    too_large: List[str]
    unreadable: List[str]
    candidates: List[str]
    filtered: List[str]


class ModelParseDiagnosticsResponse(BaseModel):
    """Response schema for model parse diagnostics."""
    file_id: str
    relpath: str
    parse_status: str  # "success", "warning", or "failure"
    parse_error_msg: Optional[str] = None
    elements_loaded: int = 0
    elements_skipped: int = 0
    parse_time_ms: int = 0
    file_size_bytes_source: int = 0
    file_size_bytes_ir: int = 0
    warning_count: int = 0
    warnings_by_type: Dict[str, int] = {}
    warning_msgs: Dict[str, List[str]] = {}
    skip_ratio: float = 0.0
    warnings_per_element: float = 0.0


class ParseResponse(BaseModel):
    """Response schema for parse endpoint."""
    dataset_root: str
    parsed_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    index: Dict[str, str]
    modelParseDiagnostics: Dict[str, ModelParseDiagnosticsResponse] = {}


class MeasureRequest(BaseModel):
    """Request schema for measure endpoint."""
    ir_dir: str = Field(..., description="Path to IR directory containing IR JSON files")
    output_dir: str = Field(..., description="Path to output directory for measures JSON files")
    profile_path: Optional[str] = Field(None, description="Optional path to benchmark profile JSON file for measure configuration")


class MeasureResponse(BaseModel):
    """Response schema for measure endpoint."""
    measures_path: str = Field(..., description="Path to measures.json file")
    measures_per_model_path: str = Field(..., description="Path to measures_per_model.json file")
    output_dir: str = Field(..., description="Output directory where measures were saved")


class ReportRequest(BaseModel):
    """Request schema for report endpoint."""
    measures_path: str = Field(..., description="Path to measures.json file")
    measures_per_model_path: str = Field(..., description="Path to measures_per_model.json file")
    ir_info_path: Optional[str] = Field(None, description="Path to ir_info.json file (optional, for linking to models)")


class ReportResponse(BaseModel):
    """Response schema for report endpoint."""
    measures: Dict[str, Any] = Field(..., description="Dataset-level measures")
    measures_per_model: Dict[str, Any] = Field(..., description="Per-model measures")
    ir_info: Optional[Dict[str, Any]] = Field(None, description="IR info for linking models")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None

