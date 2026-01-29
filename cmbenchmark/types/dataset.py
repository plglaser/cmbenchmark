"""Dataset and IR information data models."""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any

from cmbenchmark.types.parsing import ModelParseDiagnostics


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
