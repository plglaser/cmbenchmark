"""Profile configuration for benchmark runs."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TokenizerConfig:
    """Config for label tokenization + normalization."""
    name: str  # e.g. "simple_en", "split_camel", "gpt2"
    split_on_punct: bool = True
    split_camel_case: bool = True
    strip: bool = True
    lowercase: bool = False
    keep_numbers: bool = True
    collapse_whitespace: bool = True
    unicode_nfkc: bool = True
    stopword_list: Optional[str] = None  # e.g. "en_default"
    noise_token_list: Optional[str] = None  # e.g. "generic_noise_v1"


@dataclass
class LexicalProfile:
    """Which lexical measures to compute and how."""
    enabled: bool = True
    # what to treat as label-eligible
    include_nodes: bool = True
    include_edges: bool = False  # relationships as labels or not
    label_attributes: List[str] = field(default_factory=lambda: ["name"])

    # enable/disable individual D2 measures if you ever want that
    enable_d2_m1: bool = True
    enable_d2_m2: bool = True
    enable_d2_m3: bool = True
    enable_d2_m4: bool = True
    enable_d2_m5: bool = True

    tokenizer: TokenizerConfig = field(default_factory=lambda: TokenizerConfig(name="simple_en"))


@dataclass
class BenchmarkProfile:
    """Benchmark profile configuration."""
    profile_version: str = "1.0"
    name: str = "default"
    parser_language: str = "ArchiMate-Archi"  # used by parse_from_scan
    description: str = ""
    lexical: LexicalProfile = field(default_factory=LexicalProfile)
