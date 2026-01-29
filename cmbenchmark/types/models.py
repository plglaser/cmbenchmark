"""Data models for cmbenchmark outputs."""

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Any, Optional, Literal


class CannotParseError(Exception):
    """File is not in this parser's format (e.g., wrong XML root/namespace)."""
    pass


class WarningType(str, Enum):
    """Types of warnings that can occur during parsing."""
    UNKNOWN_NODE_TYPE = "UNKNOWN_NODE_TYPE"
    UNKNOWN_EDGE_TYPE = "UNKNOWN_EDGE_TYPE"
    DUPLICATE_ID = "DUPLICATE_ID"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    MISSING_ATTRIBUTE = "MISSING_ATTRIBUTE"
    OTHER = "OTHER"


ParseStatus = Literal["success", "warning", "failure"]


@dataclass
class ParserRunStats:
    """Statistics collected during a parser run."""
    
    elements_skipped: int = 0
    warning_count: int = 0
    warnings_by_type: Dict[WarningType, int] = field(default_factory=dict)
    warning_msgs: Dict[WarningType, List[str]] = field(default_factory=dict)
    
    def add_skip(self, warning_type: WarningType, message: str = ""):
        """Record a skipped element with a warning."""
        self.elements_skipped += 1
        self.add_warning(warning_type, message)
    
    def add_warning(self, warning_type: WarningType, message: str = ""):
        """Record a warning."""
        self.warning_count += 1
        self.warnings_by_type[warning_type] = \
            self.warnings_by_type.get(warning_type, 0) + 1
        
        if warning_type not in self.warning_msgs:
            self.warning_msgs[warning_type] = []
        if message:
            self.warning_msgs[warning_type].append(message)


@dataclass
class ModelParseDiagnostics:
    """Diagnostics for a single model parse operation."""
    
    file_id: str
    relpath: str
    
    parse_status: ParseStatus
    parse_error_msg: Optional[str] = None
    
    elements_loaded: int = 0
    elements_skipped: int = 0
    
    parse_time_ms: int = 0
    
    file_size_bytes_source: int = 0
    file_size_bytes_ir: int = 0
    
    warning_count: int = 0
    warnings_by_type: Dict[str, int] = field(default_factory=dict)
    warning_msgs: Dict[str, List[str]] = field(default_factory=dict)
    
    @property
    def skip_ratio(self) -> float:
        """Ratio of skipped elements to total elements."""
        denom = max(1, self.elements_loaded + self.elements_skipped)
        return self.elements_skipped / denom
    
    @property
    def warnings_per_element(self) -> float:
        """Average warnings per loaded element."""
        denom = max(1, self.elements_loaded)
        return self.warning_count / denom
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert WarningType enum keys to strings
        if isinstance(result.get("warnings_by_type"), dict):
            result["warnings_by_type"] = {
                str(k): v for k, v in result["warnings_by_type"].items()
            }
        if isinstance(result.get("warning_msgs"), dict):
            result["warning_msgs"] = {
                str(k): v for k, v in result["warning_msgs"].items()
            }
        # Add computed properties
        result["skip_ratio"] = self.skip_ratio
        result["warnings_per_element"] = self.warnings_per_element
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelParseDiagnostics":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DatasetInfo:
    """Information about a scanned dataset."""

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ParseFailure:
    """Information about a failed parse attempt."""

    relpath: str
    ir_id: Optional[str]
    error_class: str
    message: str
    parser: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParseFailure":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class IRInfo:
    """Information about parsed IR models from parse_from_scan."""

    dataset_root: str
    parsed_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    index: Dict[str, str]  # ir_id -> relpath
    modelParseDiagnostics: Dict[str, ModelParseDiagnostics] = field(default_factory=dict)  # ir_id -> diagnostics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert ModelParseDiagnostics objects to dicts
        result["modelParseDiagnostics"] = {
            k: v.to_dict() if isinstance(v, ModelParseDiagnostics) else v
            for k, v in result["modelParseDiagnostics"].items()
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IRInfo":
        """Create from dictionary."""
        diagnostics = {
            k: ModelParseDiagnostics.from_dict(v) if isinstance(v, dict) else v
            for k, v in data.get("modelParseDiagnostics", {}).items()
        }
        return cls(
            dataset_root=data["dataset_root"],
            parsed_at=data["parsed_at"],
            parameters=data["parameters"],
            totals=data["totals"],
            index=data["index"],
            modelParseDiagnostics=diagnostics,
        )


@dataclass
class MeasureResult:
    """Computed measures for IR models."""

    num_models: int
    avg_elements_per_model: float
    avg_nodes_per_model: float
    avg_edges_per_model: float
    total_elements: int
    total_nodes: int
    total_edges: int
    edge_to_node_ratio: float
    language_specific: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeasureResult":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ReportData:
    """Data structure for generated reports."""

    metrics: MeasureResult
    ir_info: IRInfo
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metrics": self.metrics.to_dict(),
            "ir_info": self.ir_info.to_dict(),
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportData":
        """Create from dictionary."""
        return cls(
            metrics=MeasureResult.from_dict(data["metrics"]),
            ir_info=IRInfo.from_dict(data["ir_info"]),
            summary=data["summary"],
        )

