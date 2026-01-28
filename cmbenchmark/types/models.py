"""Data models for cmbenchmark outputs."""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


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
        return cls(
            dataset_root=data["dataset_root"],
            parsed_at=data["parsed_at"],
            parameters=data["parameters"],
            totals=data["totals"],
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

