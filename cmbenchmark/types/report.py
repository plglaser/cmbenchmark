"""Report data models."""

from dataclasses import dataclass
from typing import Dict, Any

from cmbenchmark.types.measures import MeasureResultDataset
from cmbenchmark.types.dataset import IRInfo


@dataclass
class ReportData:
    """Data structure for generated reports."""

    metrics: MeasureResultDataset
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
            metrics=MeasureResultDataset.from_dict(data["metrics"]),
            ir_info=IRInfo.from_dict(data["ir_info"]),
            summary=data["summary"],
        )
