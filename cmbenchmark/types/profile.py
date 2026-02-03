"""Profile configuration for benchmark runs."""

from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
import json
import importlib.resources

from cmbenchmark.types.constructs import ConstructDef


class TokenizerConfig(BaseModel):
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


class LexicalProfile(BaseModel):
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


class ParseProfile(BaseModel):
    """Configuration for parsing measures."""
    enabled: bool = True  # Whether to compute parsing measures


def _get_construct_profile_path(parser_language: str) -> Optional[str]:
    """
    Get the path to the construct profile JSON file based on parser language.
    
    Args:
        parser_language: Parser language (e.g., "ArchiMate-Archi", "UML", "Ecore")
        
    Returns:
        Path to construct profile JSON file in the package, or None if not found
    """
    # Map parser languages to construct profile files
    language_to_profile = {
        "ArchiMate-Archi": "archimate_constructs.json",
        "ArchiMate-XML": "archimate_constructs.json",
        "Ecore": "ecore_constructs.json",
        # Add more mappings as needed
    }
    
    profile_file = language_to_profile.get(parser_language)
    if not profile_file:
        # For unsupported languages, return None (will result in empty constructs)
        return None
    
    try:
        # Use importlib.resources to get the file path
        # Try files() first (Python 3.9+)
        try:
            package = importlib.resources.files("cmbenchmark.measures.construct_profiles")
            file_path = package / profile_file
            if file_path.is_file():
                return str(file_path)
        except (AttributeError, TypeError):
            # Fallback to path() for older Python versions
            with importlib.resources.path("cmbenchmark.measures.construct_profiles", profile_file) as p:
                return str(p)
    except Exception:
        # Fallback: try to construct path manually
        try:
            import cmbenchmark.measures.construct_profiles as constructs_module
            module_path = Path(constructs_module.__file__).parent
            file_path = module_path / profile_file
            if file_path.exists():
                return str(file_path)
        except Exception:
            pass
    
    return None


class ConstructCoverageProfile(BaseModel):
    """Configuration for D3 construct coverage for one language."""
    enabled: bool = True
    enable_d3_m1: bool = True
    enable_d3_m2: bool = True
    enable_d3_m3: bool = True
    constructProfile: Optional[str] = None  # Path to construct profile JSON file (auto-set, not user-provided)
    
    # This will be populated when loading the profile
    language: Optional[str] = None
    constructs: Dict[str, ConstructDef] = Field(default_factory=dict)
    
    @classmethod
    def load_for_language(cls, parser_language: str, construct_config: Optional[Dict] = None) -> "ConstructCoverageProfile":
        """
        Load construct coverage profile automatically based on parser language.
        
        Args:
            parser_language: Parser language (e.g., "ArchiMate-Archi")
            construct_config: Optional construct configuration from profile (enabled, enable_d3_m1, etc.)
            
        Returns:
            ConstructCoverageProfile instance with loaded constructs
        """
        if not construct_config or not construct_config.get("enabled", True):
            return cls(enabled=False)
        
        # Get construct profile path based on language
        construct_profile_path = _get_construct_profile_path(parser_language)
        if not construct_profile_path:
            # For unsupported languages, return enabled profile with empty constructs
            return cls(
                enabled=construct_config.get("enabled", True),
                enable_d3_m1=construct_config.get("enable_d3_m1", True),
                enable_d3_m2=construct_config.get("enable_d3_m2", True),
                enable_d3_m3=construct_config.get("enable_d3_m3", True),
                constructProfile=None,
                language=parser_language,
                constructs={},
            )
        
        # Load construct profile JSON
        with open(construct_profile_path, "r", encoding="utf-8") as f:
            construct_profile_data = json.load(f)
        
        language = construct_profile_data.get("language", "Unknown")
        constructs_list = construct_profile_data.get("constructs", [])
        
        # Convert to ConstructDef objects
        constructs_dict: Dict[str, ConstructDef] = {}
        for construct_item in constructs_list:
            construct_def = ConstructDef(
                id=construct_item["id"],
                description=construct_item.get("description", ""),
                kind=construct_item["kind"],
                match_type=construct_item["match_type"],
                match_data_equals=construct_item.get("match_data_equals", {}),
                meta=construct_item.get("meta", {}),
            )
            constructs_dict[construct_def.id] = construct_def
        
        return cls(
            enabled=construct_config.get("enabled", True),
            enable_d3_m1=construct_config.get("enable_d3_m1", True),
            enable_d3_m2=construct_config.get("enable_d3_m2", True),
            enable_d3_m3=construct_config.get("enable_d3_m3", True),
            constructProfile=construct_profile_path,
            language=language,
            constructs=constructs_dict,
        )
    
    @classmethod
    def load_from_json(cls, profile_path: str, construct_profile_path: Optional[str] = None) -> "ConstructCoverageProfile":
        """
        Load construct coverage profile from JSON, including loading the construct profile.
        
        Args:
            profile_path: Path to the benchmark profile file (for resolving relative paths)
            construct_profile_path: Path to construct profile JSON file (relative or absolute)
            
        Returns:
            ConstructCoverageProfile instance with loaded constructs
        """
        profile_file = Path(profile_path).resolve()
        profile_dir = profile_file.parent
        
        # Load the benchmark profile JSON to get construct coverage config
        with open(profile_file, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        
        construct_data = profile_data.get("measure", {}).get("constructs", {})
        if not construct_data:
            # Return default if not configured
            return cls(enabled=False)
        
        # Resolve construct profile path
        construct_profile_file = construct_profile_path or construct_data.get("constructProfile")
        if not construct_profile_file:
            raise ValueError("constructProfile path not specified in profile")
        
        if not Path(construct_profile_file).is_absolute():
            construct_profile_file = str((profile_dir / construct_profile_file).resolve())
        
        # Load construct profile JSON
        with open(construct_profile_file, "r", encoding="utf-8") as f:
            construct_profile_data = json.load(f)
        
        language = construct_profile_data.get("language", "Unknown")
        constructs_list = construct_profile_data.get("constructs", [])
        
        # Convert to ConstructDef objects
        constructs_dict: Dict[str, ConstructDef] = {}
        for construct_item in constructs_list:
            construct_def = ConstructDef(
                id=construct_item["id"],
                description=construct_item.get("description", ""),
                kind=construct_item["kind"],
                match_type=construct_item["match_type"],
                match_data_equals=construct_item.get("match_data_equals", {}),
                meta=construct_item.get("meta", {}),
            )
            constructs_dict[construct_def.id] = construct_def
        
        return cls(
            enabled=construct_data.get("enabled", True),
            enable_d3_m1=construct_data.get("enable_d3_m1", True),
            enable_d3_m2=construct_data.get("enable_d3_m2", True),
            enable_d3_m3=construct_data.get("enable_d3_m3", True),
            constructProfile=construct_profile_path or construct_data.get("constructProfile"),
            language=language,
            constructs=constructs_dict,
        )


class ScanConfig(BaseModel):
    """Configuration for the scan stage."""
    dataset_path: str
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    size_limit_mb: Optional[int] = None


class ParseConfig(BaseModel):
    """Configuration for the parse stage."""
    parser_language: str


class MeasureConfig(BaseModel):
    """Configuration for the measure stage."""
    parse: ParseProfile = Field(default_factory=ParseProfile)
    lexical: LexicalProfile = Field(default_factory=LexicalProfile)
    constructs: Optional[ConstructCoverageProfile] = None


class ReportConfig(BaseModel):
    """Configuration for the report stage."""
    # Currently no specific config needed, but kept for extensibility
    # This class can be extended in the future with report-specific settings


class BenchmarkProfile(BaseModel):
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
        
        # Load construct coverage profile automatically based on parser language
        if "measure" in data and "constructs" in data["measure"] and data["measure"]["constructs"]:
            parser_language = data.get("parse", {}).get("parser_language", "")
            construct_config = data["measure"]["constructs"]
            construct_profile = ConstructCoverageProfile.load_for_language(
                parser_language=parser_language,
                construct_config=construct_config
            )
            data["measure"]["constructs"] = construct_profile
        
        return cls(**data)
