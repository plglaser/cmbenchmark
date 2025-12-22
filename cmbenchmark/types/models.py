"""Data models for cmbenchmark outputs."""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union


class CannotParseError(Exception):
    """File is not in this parser's format (e.g., wrong XML root/namespace)."""
    pass


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
class LossReportEntry:
    """Entry in the loss report for a parsed model."""

    source_file: str
    parser: str
    loss: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossReportEntry":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class LossReport:
    """Report of information lost during parsing.
    
    The loss field can be:
    - A LossTracker instance (preferred, new format)
    - A dict with 'summary' and 'events' keys (new format)
    - A dict with legacy format (backward compatible)
    """

    parser: str
    loss: Union[Dict[str, Any], Any]  # Can be LossTracker or dict
    source_relpath: Optional[str] = None
    schema_version: Optional[str] = None  # Track schema version from source model

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Handle LossTracker instance
        if hasattr(self.loss, 'to_dict'):
            loss_dict = self.loss.to_dict()
        elif isinstance(self.loss, dict):
            loss_dict = self.loss
        else:
            # Fallback: wrap in dict
            loss_dict = {"summary": {}, "events": []}
        
        result = {
            "parser": self.parser,
            "loss": loss_dict,
        }
        if self.source_relpath is not None:
            result["source_relpath"] = self.source_relpath
        if self.schema_version is not None:
            result["schema_version"] = self.schema_version
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossReport":
        """Create from dictionary."""
        return cls(
            parser=data.get("parser", ""),
            loss=data.get("loss", {}),
            source_relpath=data.get("source_relpath"),
            schema_version=data.get("schema_version")
        )


@dataclass
class ParseFailure:
    """Information about a failed parse attempt."""

    relpath: str
    ir_id: Optional[str]
    stage: str
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
    loss_summary: Dict[str, Any]
    failures: List[ParseFailure]
    index: Dict[str, str]  # ir_id -> relpath

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert ParseFailure objects to dicts
        result["failures"] = [
            f.to_dict() if isinstance(f, ParseFailure) else f
            for f in result["failures"]
        ]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IRInfo":
        """Create from dictionary."""
        failures = [
            ParseFailure.from_dict(f) if isinstance(f, dict) else f
            for f in data.get("failures", [])
        ]
        loss_summary = data.get("loss_summary", {})
        return cls(
            dataset_root=data["dataset_root"],
            parsed_at=data["parsed_at"],
            parameters=data["parameters"],
            totals=data["totals"],
            loss_summary=loss_summary,
            failures=failures,
            index=data["index"],
        )


@dataclass
class MetricsResult:
    """Computed metrics for IR models."""

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
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsResult":
        """Create from dictionary."""
        return cls(**data)


# Type alias for loss report dictionary
# Maps ir_id -> {source_relpath: str, loss: Dict[str, Any]}
LossReportDict = Dict[str, Dict[str, Any]]


@dataclass
class ReportData:
    """Data structure for generated reports."""

    metrics: MetricsResult
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
            metrics=MetricsResult.from_dict(data["metrics"]),
            ir_info=IRInfo.from_dict(data["ir_info"]),
            summary=data["summary"],
        )

