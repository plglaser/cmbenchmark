"""Profile configuration for benchmark runs."""

from pathlib import Path
from typing import List, Optional
from pydantic import Field
import json
from cmbenchmark.types.strict import StrictBaseModel


class TokenizerConfig(StrictBaseModel):
    """Config for label tokenization + normalization."""
    name: str = "simple_en"  # e.g. "simple_en", "split_camel", "gpt2"
    split_on_punct: bool = True
    split_camel_case: bool = True
    strip: bool = True
    lowercase: bool = False
    keep_numbers: bool = True
    collapse_whitespace: bool = True
    unicode_nfkc: bool = True
    stopword_list: Optional[str] = None  # e.g. "en_default"
    noise_token_list: Optional[str] = None  # e.g. "generic_noise_v1"


class LexicalProfile(StrictBaseModel):
    """Which lexical measures to compute and how."""
    enabled: bool = True
    # what to treat as label-eligible
    include_nodes: bool = True
    include_edges: bool = False  # relationships as labels or not
    label_attributes: List[str] = Field(default_factory=lambda: ["name"])

    # enable/disable individual D2 measures
    enable_d2_m1: bool = True
    enable_d2_m2: bool = True
    enable_d2_m3: bool = True
    enable_d2_m4: bool = True
    enable_d2_m5: bool = True

    tokenizer: TokenizerConfig = Field(default_factory=lambda: TokenizerConfig(name="simple_en"))


class SizeComplexityProfile(StrictBaseModel):
    """Configuration for size & complexity measures (D4)."""
    enabled: bool = True
    enable_d4_m1: bool = True
    enable_d4_m2: bool = True
    enable_d4_m3: bool = True
    enable_d4_m4: bool = True


class ParseProfile(StrictBaseModel):
    """Configuration for parsing measures."""
    enabled: bool = True  # Whether to compute parsing measures


class ConstructCoverageConfig(StrictBaseModel):
    """Configuration for D3 construct coverage (config-only)."""
    enabled: bool = True
    enable_d3_m1: bool = True
    enable_d3_m2: bool = True
    enable_d3_m3: bool = True


class ScanConfig(StrictBaseModel):
    """Configuration for the scan stage."""
    dataset_path: str
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    size_limit_mb: Optional[int] = None


class ParseConfig(StrictBaseModel):
    """Configuration for the parse stage."""
    parser_language: str


class MeasureConfig(StrictBaseModel):
    """Configuration for the measure stage."""
    parse: ParseProfile = Field(default_factory=ParseProfile)
    lexical: LexicalProfile = Field(default_factory=LexicalProfile)
    constructs: Optional[ConstructCoverageConfig] = None
    size_complexity: SizeComplexityProfile = Field(default_factory=SizeComplexityProfile)


class ReportConfig(StrictBaseModel):
    """Configuration for the report stage."""
    # Currently no specific config needed, but kept for extensibility
    # This class can be extended in the future with report-specific settings


class BenchmarkProfile(StrictBaseModel):
    """Benchmark profile configuration."""
    name: str
    version: str
    output_path: str
    scan: ScanConfig
    parse: ParseConfig
    measure: MeasureConfig = Field(default_factory=MeasureConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
    
    @classmethod
    def load_from_file(cls, profile_path: str) -> "BenchmarkProfile":
        """
        Load profile from JSON file and resolve relative paths relative to profile file location.
        
        Args:
            profile_path: Path to profile JSON file
            
        Returns:
            BenchmarkProfile instance with resolved paths
        """
        
        profile_file = Path(profile_path).resolve()
        if not profile_file.exists():
            raise FileNotFoundError(f"Profile file does not exist: {profile_path}")
        
        with open(profile_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Resolve relative paths in scan.dataset_path relative to profile file location
        profile_dir = profile_file.parent
        if "scan" in data and "dataset_path" in data["scan"]:
            dataset_path = data["scan"]["dataset_path"]
            if not Path(dataset_path).is_absolute():
                # Resolve relative to profile file location
                data["scan"]["dataset_path"] = str((profile_dir / dataset_path).resolve())
        
        # Resolve relative paths in output_path relative to profile file location
        if "output_path" in data:
            output_path = data["output_path"]
            if not Path(output_path).is_absolute():
                # Resolve relative to profile file location
                data["output_path"] = str((profile_dir / output_path).resolve())
        
        return cls(**data)
