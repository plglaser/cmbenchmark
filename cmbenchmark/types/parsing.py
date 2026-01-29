"""Parsing-related data models."""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional

from cmbenchmark.types.enums import WarningType, ParseStatus


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
