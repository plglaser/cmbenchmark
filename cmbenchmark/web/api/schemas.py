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


class ParseFailureResponse(BaseModel):
    """Response schema for parse failure."""
    relpath: str
    ir_id: Optional[str]
    stage: str
    error_class: str
    message: str
    parser: str


class ParseResponse(BaseModel):
    """Response schema for parse endpoint."""
    dataset_root: str
    parsed_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    failures: List[ParseFailureResponse]
    index: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None

