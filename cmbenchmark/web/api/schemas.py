"""Pydantic schemas for API requests and responses."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


# Request schemas
class ScanRequest(BaseModel):
    """Request schema for scan endpoint."""
    dataset_path: str = Field(..., description="Path to dataset directory")
    out: str = Field(..., description="Path to output directory for dataset_info.json")
    exclude: Optional[str] = Field(None, description="Comma-separated list of file patterns to exclude")
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
    loss_summary: Dict[str, Any]
    failures: List[ParseFailureResponse]
    index: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None

