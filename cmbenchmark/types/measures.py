"""Measure-related data models."""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List


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


# ========== D2 Lexical Quality Measures ==========

# ---------- D2.M1 — Label Presence (dataset-level) ----------
@dataclass
class D2M1LabelPresenceDataset:
    """Dataset-level D2.M1 label presence measure."""
    dataset_label_eligible_count: int
    dataset_label_present_count: int
    dataset_label_present_share: float  # micro-average
    dataset_label_missing_share: float

    # distribution across models
    label_present_share_stats: DistributionSummary
    label_missing_share_stats: DistributionSummary

    # indicator
    label_completeness_index: float  # == dataset_label_present_share
    completeness_category: str  # "high" | "moderate" | "low"

    # per-node-type missing shares (dataset level, micro-averaged)
    label_missing_share_by_type: Dict[str, float] = field(default_factory=dict)


# ---------- D2.M2 — Label Length (dataset-level) ----------
@dataclass
class D2M2LabelLengthDataset:
    """Dataset-level D2.M2 label length measure."""
    # distributions over models
    label_length_chars_median_stats: DistributionSummary
    label_length_tokens_median_stats: DistributionSummary
    short_label_share_stats: DistributionSummary  # over models
    long_label_share_stats: DistributionSummary


# ---------- D2.M3 — Naming Convention Consistency (dataset-level) ----------
@dataclass
class D2M3NamingConventionDataset:
    """Dataset-level D2.M3 naming convention measure."""
    naming_style_entropy_stats: DistributionSummary  # entropy per model
    dataset_case_style_counts: Dict[str, int] = field(default_factory=dict)
    dataset_case_style_share: Dict[str, float] = field(default_factory=dict)


# ---------- D2.M4 — Single vs Multi Word (dataset-level) ----------
@dataclass
class D2M4SingleMultiWordDataset:
    """Dataset-level D2.M4 single vs multi-word measure."""
    total_single_word_labels: int
    total_multi_word_labels: int
    dataset_share_single_word_labels: float

    share_single_word_labels_stats: DistributionSummary


# ---------- D2.M5 — Lexical Diversity (dataset-level) ----------
@dataclass
class D2M5LexicalDiversityDataset:
    """Dataset-level D2.M5 lexical diversity measure."""
    total_tokens: int
    vocab_size: int
    type_token_ratio: float
    stopword_tokens: int = 0
    stopword_share: float = 0.0


# ---------- D2.M1 per-model ----------
@dataclass
class D2M1LabelPresencePerModel:
    """Per-model D2.M1 label presence measure."""
    label_eligible_count: int
    label_present_count: int
    label_present_share: float
    label_missing_share: float
    label_missing_share_by_type: Dict[str, float] = field(default_factory=dict)


# ---------- D2.M2 per-model ----------
@dataclass
class D2M2LabelLengthPerModel:
    """Per-model D2.M2 label length measure."""
    label_count: int
    label_length_chars_mean: float
    label_length_chars_median: float
    label_length_chars_p95: float
    label_length_tokens_mean: float
    label_length_tokens_median: float
    label_length_tokens_p95: float
    short_label_share: float
    long_label_share: float


# ---------- D2.M3 per-model ----------
@dataclass
class D2M3NamingConventionPerModel:
    """Per-model D2.M3 naming convention measure."""
    case_style_counts: Dict[str, int] = field(default_factory=dict)
    case_style_share: Dict[str, float] = field(default_factory=dict)
    naming_style_entropy: float = 0.0


# ---------- D2.M4 per-model ----------
@dataclass
class D2M4SingleMultiWordPerModel:
    """Per-model D2.M4 single vs multi-word measure."""
    single_word_label_count: int
    multi_word_label_count: int
    single_word_label_share: float
    multi_word_label_share: float


# ---------- D2.M5 per-model ----------
@dataclass
class D2M5LexicalDiversityPerModel:
    """Per-model D2.M5 lexical diversity measure."""
    total_tokens: int
    vocab_size: int
    type_token_ratio: float
    stopword_tokens: int = 0
    stopword_share: float = 0.0


@dataclass
class LexicalMeasuresDataset:
    """Dataset-level lexical measures."""
    d2_m1_label_presence: D2M1LabelPresenceDataset
    d2_m2_label_length: D2M2LabelLengthDataset
    d2_m3_naming_convention: D2M3NamingConventionDataset
    d2_m4_single_multi_word: D2M4SingleMultiWordDataset
    d2_m5_lexical_diversity: D2M5LexicalDiversityDataset


# ========== D3 Construct Coverage Measures ==========

# ---------- D3.M1 — Construct Presence ----------
@dataclass
class D3M1ConstructPresencePerModel:
    """Per-model D3.M1 construct presence measure."""
    constructs_available_count: int
    constructs_observed_count: int
    coverage_share: float
    present_constructs: Dict[str, bool] = field(default_factory=dict)  # construct_id -> bool
    unknown_node_type_count: int = 0
    unknown_edge_type_count: int = 0
    unknown_type_share: float = 0.0
    unknown_type_examples: Dict[str, int] = field(default_factory=dict)  # raw_type -> count


@dataclass
class D3M1ConstructPresenceDataset:
    """Dataset-level D3.M1 construct presence measure."""
    constructs_available_count: int
    constructs_observed_count: int
    coverage_share: float
    coverage_share_stats: DistributionSummary
    unknown_type_share_dataset: float = 0.0
    # Optional additional reporting fields (newer versions)
    # - construct_id -> metadata to make UI/analysis more useful
    construct_catalog: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # - constructs never observed in the dataset
    missing_constructs: List[Dict[str, Any]] = field(default_factory=list)
    # - group breakdowns (e.g., ArchiMate layer, Ecore group)
    coverage_by_group: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    coverage_by_kind: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # - dataset-level unknown type counts
    unknown_node_type_count_dataset: int = 0
    unknown_edge_type_count_dataset: int = 0
    unknown_type_examples_dataset: Dict[str, int] = field(default_factory=dict)


# ---------- D3.M3 — Construct Frequency ----------
@dataclass
class D3M3ConstructFrequencyPerModel:
    """Per-model D3.M3 construct frequency measure."""
    count_by_construct: Dict[str, int] = field(default_factory=dict)  # construct_id -> count


@dataclass
class D3M3ConstructFrequencyDataset:
    """Dataset-level D3.M3 construct frequency measure."""
    dataset_count_by_construct: Dict[str, int] = field(default_factory=dict)  # construct_id -> total_count


@dataclass
class ConstructMeasuresDataset:
    """Dataset-level construct coverage measures."""
    d3_m1_construct_presence: D3M1ConstructPresenceDataset
    d3_m3_construct_frequency: D3M3ConstructFrequencyDataset


@dataclass
class ConstructMeasuresPerModel:
    """Per-model construct coverage measures."""
    d3_m1_construct_presence: Dict[str, D3M1ConstructPresencePerModel] = field(default_factory=dict)
    d3_m3_construct_frequency: Dict[str, D3M3ConstructFrequencyPerModel] = field(default_factory=dict)


@dataclass
class LexicalMeasuresPerModel:
    """Per-model lexical measures."""
    d2_m1_label_presence: Dict[str, D2M1LabelPresencePerModel] = field(default_factory=dict)
    d2_m2_label_length: Dict[str, D2M2LabelLengthPerModel] = field(default_factory=dict)
    d2_m3_naming_convention: Dict[str, D2M3NamingConventionPerModel] = field(default_factory=dict)
    d2_m4_single_multi_word: Dict[str, D2M4SingleMultiWordPerModel] = field(default_factory=dict)
    d2_m5_lexical_diversity: Dict[str, D2M5LexicalDiversityPerModel] = field(default_factory=dict)


@dataclass
class MeasureResultDataset:
    """Dataset-level computed measures for IR models."""
    num_models: int
    parsing: ParsingMeasuresDataset
    lexical: Optional["LexicalMeasuresDataset"] = None
    constructs: Optional["ConstructMeasuresDataset"] = None

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
        
        # Convert lexical measures if present
        lexical = None
        lexical_data = data.get("lexical")
        if lexical_data:
            d2_m1_data = lexical_data.get("d2_m1_label_presence", {})
            d2_m2_data = lexical_data.get("d2_m2_label_length", {})
            d2_m3_data = lexical_data.get("d2_m3_naming_convention", {})
            d2_m4_data = lexical_data.get("d2_m4_single_multi_word", {})
            d2_m5_data = lexical_data.get("d2_m5_lexical_diversity", {})
            
            # Convert DistributionSummary dicts to objects
            if isinstance(d2_m1_data.get("label_present_share_stats"), dict):
                d2_m1_data["label_present_share_stats"] = _to_distribution_summary(d2_m1_data["label_present_share_stats"])
            if isinstance(d2_m1_data.get("label_missing_share_stats"), dict):
                d2_m1_data["label_missing_share_stats"] = _to_distribution_summary(d2_m1_data["label_missing_share_stats"])
            if isinstance(d2_m2_data.get("label_length_chars_median_stats"), dict):
                d2_m2_data["label_length_chars_median_stats"] = _to_distribution_summary(d2_m2_data["label_length_chars_median_stats"])
            if isinstance(d2_m2_data.get("label_length_tokens_median_stats"), dict):
                d2_m2_data["label_length_tokens_median_stats"] = _to_distribution_summary(d2_m2_data["label_length_tokens_median_stats"])
            if isinstance(d2_m2_data.get("short_label_share_stats"), dict):
                d2_m2_data["short_label_share_stats"] = _to_distribution_summary(d2_m2_data["short_label_share_stats"])
            if isinstance(d2_m2_data.get("long_label_share_stats"), dict):
                d2_m2_data["long_label_share_stats"] = _to_distribution_summary(d2_m2_data["long_label_share_stats"])
            if isinstance(d2_m3_data.get("naming_style_entropy_stats"), dict):
                d2_m3_data["naming_style_entropy_stats"] = _to_distribution_summary(d2_m3_data["naming_style_entropy_stats"])
            if isinstance(d2_m4_data.get("share_single_word_labels_stats"), dict):
                d2_m4_data["share_single_word_labels_stats"] = _to_distribution_summary(d2_m4_data["share_single_word_labels_stats"])
            
            lexical = LexicalMeasuresDataset(
                d2_m1_label_presence=D2M1LabelPresenceDataset(**d2_m1_data),
                d2_m2_label_length=D2M2LabelLengthDataset(**d2_m2_data),
                d2_m3_naming_convention=D2M3NamingConventionDataset(**d2_m3_data),
                d2_m4_single_multi_word=D2M4SingleMultiWordDataset(**d2_m4_data),
                d2_m5_lexical_diversity=D2M5LexicalDiversityDataset(**d2_m5_data),
            )
        
        # Convert construct measures if present
        constructs = None
        constructs_data = data.get("constructs")
        if constructs_data:
            d3_m1_data = constructs_data.get("d3_m1_construct_presence", {})
            d3_m3_data = constructs_data.get("d3_m3_construct_frequency", {})
            
            # Convert DistributionSummary dicts to objects
            if isinstance(d3_m1_data.get("coverage_share_stats"), dict):
                d3_m1_data["coverage_share_stats"] = _to_distribution_summary(d3_m1_data["coverage_share_stats"])
            
            constructs = ConstructMeasuresDataset(
                d3_m1_construct_presence=D3M1ConstructPresenceDataset(**d3_m1_data),
                d3_m3_construct_frequency=D3M3ConstructFrequencyDataset(**d3_m3_data),
            )
        
        return cls(
            num_models=data["num_models"],
            parsing=parsing,
            lexical=lexical,
            constructs=constructs,
        )


@dataclass
class MeasureResultPerModel:
    """Per-model computed measures for IR models."""
    parsing: ParsingMeasuresPerModel
    lexical: Optional["LexicalMeasuresPerModel"] = None
    constructs: Optional["ConstructMeasuresPerModel"] = None

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
        
        # Convert lexical measures if present
        lexical = None
        lexical_data = data.get("lexical")
        if lexical_data:
            def _to_lexical_per_model_dict(measure_name: str, per_model_class: type) -> Dict[str, Any]:
                """Convert dict of per-model lexical data to typed objects."""
                result = {}
                for model_id, model_data in lexical_data.get(measure_name, {}).items():
                    if isinstance(model_data, dict):
                        result[model_id] = per_model_class(**model_data)
                    else:
                        result[model_id] = model_data
                return result
            
            lexical = LexicalMeasuresPerModel(
                d2_m1_label_presence=_to_lexical_per_model_dict("d2_m1_label_presence", D2M1LabelPresencePerModel),
                d2_m2_label_length=_to_lexical_per_model_dict("d2_m2_label_length", D2M2LabelLengthPerModel),
                d2_m3_naming_convention=_to_lexical_per_model_dict("d2_m3_naming_convention", D2M3NamingConventionPerModel),
                d2_m4_single_multi_word=_to_lexical_per_model_dict("d2_m4_single_multi_word", D2M4SingleMultiWordPerModel),
                d2_m5_lexical_diversity=_to_lexical_per_model_dict("d2_m5_lexical_diversity", D2M5LexicalDiversityPerModel),
            )
        
        # Convert construct measures if present
        constructs = None
        constructs_data = data.get("constructs")
        if constructs_data:
            def _to_construct_per_model_dict(measure_name: str, per_model_class: type) -> Dict[str, Any]:
                """Convert dict of per-model construct data to typed objects."""
                result = {}
                for model_id, model_data in constructs_data.get(measure_name, {}).items():
                    if isinstance(model_data, dict):
                        result[model_id] = per_model_class(**model_data)
                    else:
                        result[model_id] = model_data
                return result
            
            constructs = ConstructMeasuresPerModel(
                d3_m1_construct_presence=_to_construct_per_model_dict("d3_m1_construct_presence", D3M1ConstructPresencePerModel),
                d3_m3_construct_frequency=_to_construct_per_model_dict("d3_m3_construct_frequency", D3M3ConstructFrequencyPerModel),
            )
        
        return cls(parsing=parsing, lexical=lexical, constructs=constructs)
