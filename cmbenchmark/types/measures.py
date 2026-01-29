"""Measure-related data models."""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional


@dataclass
class DistributionSummary:
    """Summary statistics for a distribution."""
    n: int
    min: float
    p25: float
    median: float
    mean: float
    p75: float
    max: float
    std: float


# D1.M1 — Parse Status
@dataclass
class D1M1ParseStatusResult:
    """Result for D1.M1 parse status measure."""
    n_models: int
    n_success: int
    n_partial: int
    n_failed: int
    share_success: float
    share_partial: float
    share_failed: float
    parsing_robustness_index: float


# D1.M2 — Elements Loaded vs. Skipped
@dataclass
class D1M2ElementsLoadedSkippedResult:
    """Result for D1.M2 elements loaded vs skipped measure."""
    total_elements_loaded: int
    total_elements_skipped: int
    dataset_skip_ratio: float
    skip_ratio_stats: DistributionSummary
    n_models_with_skips: int
    share_models_with_skips: float


# D1.M3 — Parsing Time
@dataclass
class D1M3ParsingTimeResult:
    """Result for D1.M3 parsing time measure."""
    parse_time_stats: DistributionSummary
    parse_time_total_ms: int


# D1.M4 — File Size
@dataclass
class D1M4FileSizeResult:
    """Result for D1.M4 file size measure."""
    file_size_source_stats: DistributionSummary
    file_size_ir_stats: DistributionSummary


# D1.M5 — Warnings
@dataclass
class D1M5WarningsResult:
    """Result for D1.M5 warnings measure."""
    n_models_with_warnings: int
    share_models_with_warnings: float
    warning_count_stats: DistributionSummary
    warnings_per_element_stats: DistributionSummary
    total_warnings_by_type: Dict[str, int] = field(default_factory=dict)
    n_models_with_warning_type: Dict[str, int] = field(default_factory=dict)
    share_models_with_warning_type: Dict[str, float] = field(default_factory=dict)


# Per-model entry dataclasses
@dataclass
class D1M1ParseStatusPerModel:
    """Per-model parse status."""
    parse_status: str
    parse_error_msg: Optional[str] = None


@dataclass
class D1M2ElementsLoadedSkippedPerModel:
    """Per-model elements loaded/skipped."""
    elements_loaded: int
    elements_skipped: int
    skip_ratio: float


@dataclass
class D1M3ParsingTimePerModel:
    """Per-model parsing time."""
    parse_time_ms: int


@dataclass
class D1M4FileSizePerModel:
    """Per-model file size."""
    file_size_bytes_source: int
    file_size_bytes_ir: int


@dataclass
class D1M5WarningsPerModel:
    """Per-model warnings."""
    warning_count: int
    warnings_by_type: Dict[str, int] = field(default_factory=dict)
    warnings_per_element: float = 0.0


@dataclass
class ParsingMeasuresDataset:
    """Dataset-level parsing measures."""
    d1_m1_parse_status: D1M1ParseStatusResult
    d1_m2_elements_loaded_skipped: D1M2ElementsLoadedSkippedResult
    d1_m3_parsing_time: D1M3ParsingTimeResult
    d1_m4_file_size: D1M4FileSizeResult
    d1_m5_warnings: D1M5WarningsResult


@dataclass
class ParsingMeasuresPerModel:
    """Per-model parsing measures."""
    d1_m1_parse_status: Dict[str, D1M1ParseStatusPerModel] = field(default_factory=dict)
    d1_m2_elements_loaded_skipped: Dict[str, D1M2ElementsLoadedSkippedPerModel] = field(default_factory=dict)
    d1_m3_parsing_time: Dict[str, D1M3ParsingTimePerModel] = field(default_factory=dict)
    d1_m4_file_size: Dict[str, D1M4FileSizePerModel] = field(default_factory=dict)
    d1_m5_warnings: Dict[str, D1M5WarningsPerModel] = field(default_factory=dict)


@dataclass
class MeasureResultDataset:
    """Dataset-level computed measures for IR models."""
    num_models: int
    avg_elements_per_model: float
    avg_nodes_per_model: float
    avg_edges_per_model: float
    total_elements: int
    total_nodes: int
    total_edges: int
    edge_to_node_ratio: float
    language_specific: Dict[str, Any]
    parsing: ParsingMeasuresDataset

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeasureResultDataset":
        """Create from dictionary."""
        parsing_data = data.get("parsing", {})
        
        # Helper function to convert dict to DistributionSummary if needed
        def _to_distribution_summary(obj: Any) -> DistributionSummary:
            if isinstance(obj, dict):
                return DistributionSummary(**obj)
            return obj
        
        # Convert parsing measures
        d1_m1_data = parsing_data.get("d1_m1_parse_status", {})
        d1_m2_data = parsing_data.get("d1_m2_elements_loaded_skipped", {})
        d1_m3_data = parsing_data.get("d1_m3_parsing_time", {})
        d1_m4_data = parsing_data.get("d1_m4_file_size", {})
        d1_m5_data = parsing_data.get("d1_m5_warnings", {})
        
        # Convert DistributionSummary dicts to objects
        if isinstance(d1_m2_data.get("skip_ratio_stats"), dict):
            d1_m2_data["skip_ratio_stats"] = _to_distribution_summary(d1_m2_data["skip_ratio_stats"])
        if isinstance(d1_m3_data.get("parse_time_stats"), dict):
            d1_m3_data["parse_time_stats"] = _to_distribution_summary(d1_m3_data["parse_time_stats"])
        if isinstance(d1_m4_data.get("file_size_source_stats"), dict):
            d1_m4_data["file_size_source_stats"] = _to_distribution_summary(d1_m4_data["file_size_source_stats"])
        if isinstance(d1_m4_data.get("file_size_ir_stats"), dict):
            d1_m4_data["file_size_ir_stats"] = _to_distribution_summary(d1_m4_data["file_size_ir_stats"])
        if isinstance(d1_m5_data.get("warning_count_stats"), dict):
            d1_m5_data["warning_count_stats"] = _to_distribution_summary(d1_m5_data["warning_count_stats"])
        if isinstance(d1_m5_data.get("warnings_per_element_stats"), dict):
            d1_m5_data["warnings_per_element_stats"] = _to_distribution_summary(d1_m5_data["warnings_per_element_stats"])
        
        parsing = ParsingMeasuresDataset(
            d1_m1_parse_status=D1M1ParseStatusResult(**d1_m1_data),
            d1_m2_elements_loaded_skipped=D1M2ElementsLoadedSkippedResult(**d1_m2_data),
            d1_m3_parsing_time=D1M3ParsingTimeResult(**d1_m3_data),
            d1_m4_file_size=D1M4FileSizeResult(**d1_m4_data),
            d1_m5_warnings=D1M5WarningsResult(**d1_m5_data),
        )
        
        return cls(
            num_models=data["num_models"],
            avg_elements_per_model=data["avg_elements_per_model"],
            avg_nodes_per_model=data["avg_nodes_per_model"],
            avg_edges_per_model=data["avg_edges_per_model"],
            total_elements=data["total_elements"],
            total_nodes=data["total_nodes"],
            total_edges=data["total_edges"],
            edge_to_node_ratio=data["edge_to_node_ratio"],
            language_specific=data["language_specific"],
            parsing=parsing,
        )


@dataclass
class MeasureResultPerModel:
    """Per-model computed measures for IR models."""
    parsing: ParsingMeasuresPerModel

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeasureResultPerModel":
        """Create from dictionary."""
        parsing_data = data.get("parsing", {})
        
        def _to_per_model_dict(measure_name: str, per_model_class: type) -> Dict[str, Any]:
            """Convert dict of per-model data to typed objects."""
            result = {}
            for model_id, model_data in parsing_data.get(measure_name, {}).items():
                if isinstance(model_data, dict):
                    result[model_id] = per_model_class(**model_data)
                else:
                    result[model_id] = model_data
            return result
        
        parsing = ParsingMeasuresPerModel(
            d1_m1_parse_status=_to_per_model_dict("d1_m1_parse_status", D1M1ParseStatusPerModel),
            d1_m2_elements_loaded_skipped=_to_per_model_dict("d1_m2_elements_loaded_skipped", D1M2ElementsLoadedSkippedPerModel),
            d1_m3_parsing_time=_to_per_model_dict("d1_m3_parsing_time", D1M3ParsingTimePerModel),
            d1_m4_file_size=_to_per_model_dict("d1_m4_file_size", D1M4FileSizePerModel),
            d1_m5_warnings=_to_per_model_dict("d1_m5_warnings", D1M5WarningsPerModel),
        )
        
        return cls(parsing=parsing)
