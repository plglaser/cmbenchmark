"""Computation functions for lexical quality measures (D2)."""

import re
import statistics
import unicodedata
from typing import List, Tuple, Dict, Optional, Protocol
from collections import Counter

from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.measures import (
    LexicalMeasuresDataset,
    LexicalMeasuresPerModel,
    D2M1LabelPresenceDataset,
    D2M1LabelPresencePerModel,
    D2M2LabelLengthDataset,
    D2M2LabelLengthPerModel,
    D2M3NamingConventionDataset,
    D2M3NamingConventionPerModel,
    D2M4SingleMultiWordDataset,
    D2M4SingleMultiWordPerModel,
    D2M5LexicalDiversityDataset,
    D2M5LexicalDiversityPerModel,
    DistributionSummary,
)
from cmbenchmark.types.profile import LexicalProfile, TokenizerConfig
from cmbenchmark.measures.parsing_measures import _compute_distribution_summary, _compute_percentile


class LabelTokenizer(Protocol):
    """Protocol for label tokenizers."""
    def tokenize(self, text: str) -> List[str]:
        """Tokenize a text label into a list of tokens."""
        ...
    
    @property
    def name(self) -> str:
        """Name of the tokenizer."""
        ...


class SimpleTokenizer:
    """Simple tokenizer implementation based on TokenizerConfig."""
    
    def __init__(self, config: TokenizerConfig):
        self.config = config
        self._stopwords: Optional[set] = None
        self._noise_tokens: Optional[set] = None
        
        # Load stopwords if specified
        if config.stopword_list:
            # For now, we'll use a simple default English stopword list
            # In a full implementation, this would load from a resource file
            if config.stopword_list == "en_default":
                self._stopwords = {
                    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
                    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
                    "been", "being", "have", "has", "had", "do", "does", "did", "will",
                    "would", "should", "could", "may", "might", "must", "can", "this",
                    "that", "these", "those", "it", "its", "they", "them", "their",
                }
        
        # Load noise tokens if specified
        if config.noise_token_list:
            if config.noise_token_list == "generic_noise_v1":
                self._noise_tokens = {
                    "", " ", "\t", "\n", "\r", "-", "_", ".", ",", ";", ":", "!", "?",
                }
    
    @property
    def name(self) -> str:
        return self.config.name
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text according to configuration."""
        if not text:
            return []
        
        # Unicode normalization
        if self.config.unicode_nfkc:
            text = unicodedata.normalize("NFKC", text)
        
        # Strip whitespace
        if self.config.strip:
            text = text.strip()
        
        # Collapse whitespace
        if self.config.collapse_whitespace:
            text = re.sub(r'\s+', ' ', text)
        
        # Lowercase
        if self.config.lowercase:
            text = text.lower()
        
        # Split camel case
        if self.config.split_camel_case:
            text = self._split_camel_case(text)
        
        # Split on punctuation
        if self.config.split_on_punct:
            # Split on punctuation but keep tokens
            tokens = re.split(r'[\s\W_]+', text)
        else:
            # Split only on whitespace
            tokens = text.split()
        
        # Filter empty tokens
        tokens = [t for t in tokens if t]
        
        # Remove numbers if not keeping them
        if not self.config.keep_numbers:
            tokens = [t for t in tokens if not t.isdigit()]
        
        # Filter stopwords
        if self._stopwords:
            tokens = [t for t in tokens if t not in self._stopwords]
        
        # Filter noise tokens
        if self._noise_tokens:
            tokens = [t for t in tokens if t not in self._noise_tokens]
        
        return tokens
    
    def _split_camel_case(self, text: str) -> str:
        """Insert spaces before capital letters in camelCase."""
        # Pattern: lowercase or digit followed by uppercase
        return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)


def build_tokenizer(cfg: TokenizerConfig) -> LabelTokenizer:
    """Build a tokenizer from configuration."""
    return SimpleTokenizer(cfg)


def _extract_labels(ir: IR, profile: LexicalProfile) -> List[Tuple[str, str, str]]:
    """
    Extract labels from IR according to profile.
    
    Returns:
        List of (label_text, element_type, element_id) tuples
    """
    labels = []
    
    if profile.include_nodes:
        for node in ir.nodes:
            for attr in profile.label_attributes:
                if hasattr(node, attr):
                    label_text = getattr(node, attr)
                    if label_text and isinstance(label_text, str):
                        labels.append((label_text, node.type, node.id))
                elif attr in node.data:
                    label_text = node.data[attr]
                    if label_text and isinstance(label_text, str):
                        labels.append((label_text, node.type, node.id))
    
    if profile.include_edges:
        for edge in ir.edges:
            for attr in profile.label_attributes:
                # Check if attribute exists on edge object (e.g., type)
                if hasattr(edge, attr):
                    label_text = getattr(edge, attr)
                    if label_text and isinstance(label_text, str):
                        labels.append((label_text, edge.type, edge.id))
                # Check if attribute exists in edge.data dict
                elif attr in edge.data:
                    label_text = edge.data[attr]
                    if label_text and isinstance(label_text, str):
                        labels.append((label_text, edge.type, edge.id))
    
    return labels


def _detect_case_style(text: str) -> str:
    """Detect the case style of a text label."""
    if not text:
        return "empty"
    
    # Check for camelCase
    if re.match(r'^[a-z][a-zA-Z0-9]*$', text) and any(c.isupper() for c in text):
        return "camelCase"
    
    # Check for PascalCase
    if re.match(r'^[A-Z][a-zA-Z0-9]*$', text) and any(c.islower() for c in text):
        return "PascalCase"
    
    # Check for snake_case
    if '_' in text and text.replace('_', '').isalnum():
        return "snake_case"
    
    # Check for kebab-case
    if '-' in text and text.replace('-', '').isalnum():
        return "kebab-case"
    
    # Check for UPPER_CASE
    if text.isupper() and '_' in text:
        return "UPPER_CASE"
    
    # Check for lowercase
    if text.islower():
        return "lowercase"
    
    # Check for UPPERCASE (no underscores)
    if text.isupper() and text.isalpha():
        return "UPPERCASE"
    
    # Mixed or other
    return "mixed"


def _compute_entropy(counts: Dict[str, int]) -> float:
    """Compute Shannon entropy from counts."""
    import math
    total = sum(counts.values())
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def compute_lexical_measures(
    ir_models: List[IR],
    lexical_profile: LexicalProfile,
) -> Tuple[LexicalMeasuresDataset, LexicalMeasuresPerModel]:
    """
    Compute lexical quality measures (D2.M1-D2.M5) for IR models.
    
    Args:
        ir_models: List of IR models to analyze
        lexical_profile: Configuration for lexical measures
        
    Returns:
        Tuple of (dataset_measures, per_model_measures)
    """
    tokenizer = build_tokenizer(lexical_profile.tokenizer)
    
    # Per-model accumulators
    per_model_d2m1: Dict[str, D2M1LabelPresencePerModel] = {}
    per_model_d2m2: Dict[str, D2M2LabelLengthPerModel] = {}
    per_model_d2m3: Dict[str, D2M3NamingConventionPerModel] = {}
    per_model_d2m4: Dict[str, D2M4SingleMultiWordPerModel] = {}
    per_model_d2m5: Dict[str, D2M5LexicalDiversityPerModel] = {}
    
    # Dataset-level accumulators
    dataset_label_eligible_count = 0
    dataset_label_present_count = 0
    label_missing_by_type: Dict[str, int] = {}
    label_eligible_by_type: Dict[str, int] = {}
    
    # For D2.M2: collect medians per model
    label_length_chars_medians: List[float] = []
    label_length_tokens_medians: List[float] = []
    short_label_shares: List[float] = []
    long_label_shares: List[float] = []
    
    # For D2.M3: collect entropies per model
    naming_style_entropies: List[float] = []
    dataset_case_style_counts: Counter[str] = Counter()
    
    # For D2.M4: collect shares per model
    share_single_word_labels: List[float] = []
    total_single_word_labels = 0
    total_multi_word_labels = 0
    
    # For D2.M5: aggregate tokens across all models
    all_tokens: List[str] = []
    all_stopword_tokens = 0
    
    # Process each IR model
    for ir in ir_models:
        labels = _extract_labels(ir, lexical_profile)
        
        # D2.M1: Label Presence
        eligible_count = len(labels)
        present_count = sum(1 for label_text, _, _ in labels if label_text and label_text.strip())
        present_share = present_count / eligible_count if eligible_count > 0 else 0.0
        missing_share = 1.0 - present_share
        
        # Per-type missing shares
        missing_by_type: Dict[str, int] = {}
        eligible_by_type: Dict[str, int] = {}
        for label_text, elem_type, _ in labels:
            eligible_by_type[elem_type] = eligible_by_type.get(elem_type, 0) + 1
            if not label_text or not label_text.strip():
                missing_by_type[elem_type] = missing_by_type.get(elem_type, 0) + 1
        
        missing_share_by_type = {
            elem_type: missing_by_type.get(elem_type, 0) / eligible_by_type.get(elem_type, 1)
            for elem_type in eligible_by_type.keys()
        }
        
        per_model_d2m1[ir.id] = D2M1LabelPresencePerModel(
            label_eligible_count=eligible_count,
            label_present_count=present_count,
            label_present_share=present_share,
            label_missing_share=missing_share,
            label_missing_share_by_type=missing_share_by_type,
        )
        
        dataset_label_eligible_count += eligible_count
        dataset_label_present_count += present_count
        for elem_type, count in eligible_by_type.items():
            label_eligible_by_type[elem_type] = label_eligible_by_type.get(elem_type, 0) + count
        for elem_type, count in missing_by_type.items():
            label_missing_by_type[elem_type] = label_missing_by_type.get(elem_type, 0) + count
        
        # D2.M2: Label Length
        present_labels = [(label_text, elem_type) for label_text, elem_type, _ in labels if label_text and label_text.strip()]
        
        if present_labels:
            label_lengths_chars = [len(label_text) for label_text, _ in present_labels]
            label_lengths_tokens = [len(tokenizer.tokenize(label_text)) for label_text, _ in present_labels]
            
            chars_mean = statistics.mean(label_lengths_chars)
            chars_median = statistics.median(label_lengths_chars)
            chars_p95 = _compute_percentile(label_lengths_chars, 95)
            
            tokens_mean = statistics.mean(label_lengths_tokens)
            tokens_median = statistics.median(label_lengths_tokens)
            tokens_p95 = _compute_percentile(label_lengths_tokens, 95)
            
            # Short labels: < 5 chars or < 2 tokens
            short_count = sum(1 for c, t in zip(label_lengths_chars, label_lengths_tokens) if c < 5 or t < 2)
            short_share = short_count / len(present_labels)
            
            # Long labels: > 30 chars or > 8 tokens
            long_count = sum(1 for c, t in zip(label_lengths_chars, label_lengths_tokens) if c > 30 or t > 8)
            long_share = long_count / len(present_labels)
            
            per_model_d2m2[ir.id] = D2M2LabelLengthPerModel(
                label_count=len(present_labels),
                label_length_chars_mean=chars_mean,
                label_length_chars_median=chars_median,
                label_length_chars_p95=chars_p95,
                label_length_tokens_mean=tokens_mean,
                label_length_tokens_median=tokens_median,
                label_length_tokens_p95=tokens_p95,
                short_label_share=short_share,
                long_label_share=long_share,
            )
            
            label_length_chars_medians.append(chars_median)
            label_length_tokens_medians.append(tokens_median)
            short_label_shares.append(short_share)
            long_label_shares.append(long_share)
        else:
            per_model_d2m2[ir.id] = D2M2LabelLengthPerModel(
                label_count=0,
                label_length_chars_mean=0.0,
                label_length_chars_median=0.0,
                label_length_chars_p95=0.0,
                label_length_tokens_mean=0.0,
                label_length_tokens_median=0.0,
                label_length_tokens_p95=0.0,
                short_label_share=0.0,
                long_label_share=0.0,
            )
        
        # D2.M3: Naming Convention
        case_style_counts: Counter[str] = Counter()
        for label_text, _ in present_labels:
            case_style = _detect_case_style(label_text)
            case_style_counts[case_style] += 1
            dataset_case_style_counts[case_style] += 1
        
        case_style_share = {
            style: count / len(present_labels) if present_labels else 0.0
            for style, count in case_style_counts.items()
        }
        
        entropy = _compute_entropy(dict(case_style_counts))
        naming_style_entropies.append(entropy)
        
        per_model_d2m3[ir.id] = D2M3NamingConventionPerModel(
            case_style_counts=dict(case_style_counts),
            case_style_share=case_style_share,
            naming_style_entropy=entropy,
        )
        
        # D2.M4: Single vs Multi Word
        single_word_count = 0
        multi_word_count = 0
        
        for label_text, _ in present_labels:
            tokens = tokenizer.tokenize(label_text)
            if len(tokens) == 1:
                single_word_count += 1
            elif len(tokens) > 1:
                multi_word_count += 1
        
        total_labels = single_word_count + multi_word_count
        single_word_share = single_word_count / total_labels if total_labels > 0 else 0.0
        multi_word_share = multi_word_count / total_labels if total_labels > 0 else 0.0
        
        per_model_d2m4[ir.id] = D2M4SingleMultiWordPerModel(
            single_word_label_count=single_word_count,
            multi_word_label_count=multi_word_count,
            single_word_label_share=single_word_share,
            multi_word_label_share=multi_word_share,
        )
        
        share_single_word_labels.append(single_word_share)
        total_single_word_labels += single_word_count
        total_multi_word_labels += multi_word_count
        
        # D2.M5: Lexical Diversity
        model_tokens: List[str] = []
        for label_text, _ in present_labels:
            tokens = tokenizer.tokenize(label_text)
            model_tokens.extend(tokens)
            all_tokens.extend(tokens)
        
        vocab_size = len(set(model_tokens))
        total_tokens = len(model_tokens)
        ttr = vocab_size / total_tokens if total_tokens > 0 else 0.0
        
        # Count stopwords (if tokenizer has them)
        stopword_count = 0
        if hasattr(tokenizer, '_stopwords') and tokenizer._stopwords:
            stopword_count = sum(1 for t in model_tokens if t in tokenizer._stopwords)
            all_stopword_tokens += stopword_count
        
        stopword_share = stopword_count / total_tokens if total_tokens > 0 else 0.0
        
        per_model_d2m5[ir.id] = D2M5LexicalDiversityPerModel(
            total_tokens=total_tokens,
            vocab_size=vocab_size,
            type_token_ratio=ttr,
            stopword_tokens=stopword_count,
            stopword_share=stopword_share,
        )
    
    # Build dataset-level measures
    dataset_label_present_share = dataset_label_present_count / dataset_label_eligible_count if dataset_label_eligible_count > 0 else 0.0
    dataset_label_missing_share = 1.0 - dataset_label_present_share
    
    # Completeness category
    if dataset_label_missing_share <= 0.1:
        completeness_category = "high"
    elif dataset_label_missing_share <= 0.25:
        completeness_category = "moderate"
    else:
        completeness_category = "low"
    
    # Label missing share by type (dataset level)
    label_missing_share_by_type = {
        elem_type: label_missing_by_type.get(elem_type, 0) / label_eligible_by_type.get(elem_type, 1)
        for elem_type in label_eligible_by_type.keys()
    }
    
    # Collect present/missing shares per model for stats
    label_present_shares = [m.label_present_share for m in per_model_d2m1.values()]
    label_missing_shares = [m.label_missing_share for m in per_model_d2m1.values()]
    
    d2m1_dataset = D2M1LabelPresenceDataset(
        dataset_label_eligible_count=dataset_label_eligible_count,
        dataset_label_present_count=dataset_label_present_count,
        dataset_label_present_share=dataset_label_present_share,
        dataset_label_missing_share=dataset_label_missing_share,
        label_present_share_stats=_compute_distribution_summary(label_present_shares),
        label_missing_share_stats=_compute_distribution_summary(label_missing_shares),
        label_completeness_index=dataset_label_present_share,
        completeness_category=completeness_category,
        label_missing_share_by_type=label_missing_share_by_type,
    )
    
    d2m2_dataset = D2M2LabelLengthDataset(
        label_length_chars_median_stats=_compute_distribution_summary(label_length_chars_medians),
        label_length_tokens_median_stats=_compute_distribution_summary(label_length_tokens_medians),
        short_label_share_stats=_compute_distribution_summary(short_label_shares),
        long_label_share_stats=_compute_distribution_summary(long_label_shares),
    )
    
    dataset_case_style_share = {
        style: count / sum(dataset_case_style_counts.values()) if dataset_case_style_counts else 0.0
        for style, count in dataset_case_style_counts.items()
    }
    
    d2m3_dataset = D2M3NamingConventionDataset(
        naming_style_entropy_stats=_compute_distribution_summary(naming_style_entropies),
        dataset_case_style_counts=dict(dataset_case_style_counts),
        dataset_case_style_share=dataset_case_style_share,
    )
    
    dataset_share_single_word = total_single_word_labels / (total_single_word_labels + total_multi_word_labels) if (total_single_word_labels + total_multi_word_labels) > 0 else 0.0
    
    d2m4_dataset = D2M4SingleMultiWordDataset(
        total_single_word_labels=total_single_word_labels,
        total_multi_word_labels=total_multi_word_labels,
        dataset_share_single_word_labels=dataset_share_single_word,
        share_single_word_labels_stats=_compute_distribution_summary(share_single_word_labels),
    )
    
    vocab_size = len(set(all_tokens))
    total_tokens = len(all_tokens)
    ttr = vocab_size / total_tokens if total_tokens > 0 else 0.0
    stopword_share = all_stopword_tokens / total_tokens if total_tokens > 0 else 0.0
    
    d2m5_dataset = D2M5LexicalDiversityDataset(
        total_tokens=total_tokens,
        vocab_size=vocab_size,
        type_token_ratio=ttr,
        stopword_tokens=all_stopword_tokens,
        stopword_share=stopword_share,
    )
    
    dataset_measures = LexicalMeasuresDataset(
        d2_m1_label_presence=d2m1_dataset,
        d2_m2_label_length=d2m2_dataset,
        d2_m3_naming_convention=d2m3_dataset,
        d2_m4_single_multi_word=d2m4_dataset,
        d2_m5_lexical_diversity=d2m5_dataset,
    )
    
    per_model_measures = LexicalMeasuresPerModel(
        d2_m1_label_presence=per_model_d2m1,
        d2_m2_label_length=per_model_d2m2,
        d2_m3_naming_convention=per_model_d2m3,
        d2_m4_single_multi_word=per_model_d2m4,
        d2_m5_lexical_diversity=per_model_d2m5,
    )
    
    return dataset_measures, per_model_measures
