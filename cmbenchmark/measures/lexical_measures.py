"""Computation functions for lexical quality measures (D2)."""

import re
import statistics
import unicodedata
from typing import List, Tuple, Dict, Optional, Protocol, Callable, Iterable
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
    D2M6LanguageUsageDataset,
    D2M6LanguageUsagePerModel,
    DistributionSummary,
)
from cmbenchmark.types.profile import LexicalProfile, TokenizerConfig
from cmbenchmark.measures.parsing_measures import _compute_distribution_summary, _compute_percentile
from cmbenchmark.measures.labels import iter_labels

# D2.M1 counts "label presence", so purely value-carrying UML nodes should not
# be treated as label-eligible slots. Keep this filter M1-local; other lexical
# measures still consume the full label stream.
_D2_M1_EXCLUDED_UML_NODE_TYPES = frozenset(
    {
        "LiteralBoolean",
        "LiteralInteger",
        "LiteralReal",
        "LiteralString",
        "LiteralUnlimitedNatural",
        "Region",
        "Expression",
        "InstanceValue",
        "InteractionOperand",
        "ClassifierTemplateParameter",
        "CombinedFragment",
        "RedefinableTemplateSignature",
        "MessageOccurrenceSpecification",
        "ExecutionOccurrenceSpecification",
        "BehaviorExecutionSpecification",
    }
)


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
    """Simple tokenizer implementation based on TokenizerConfig.

    Implements the :class:`LabelTokenizer` protocol exactly — no extra surface
    area. Stopword filtering is no longer a tokenizer concern; downstream
    measures that need stopword analysis own their own resources.
    """

    def __init__(self, config: TokenizerConfig):
        self.config = config

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

        # Split camel case
        if self.config.split_camel_case:
            text = self._split_camel_case(text)

        # Lowercase after camel-case splitting so case boundaries are preserved.
        if self.config.lowercase:
            text = text.lower()

        # Split on punctuation
        if self.config.split_on_punct:
            tokens = re.split(r'[\s\W_]+', text)
        else:
            tokens = text.split()

        # Filter empty tokens
        tokens = [t for t in tokens if t]

        # Remove numbers if not keeping them
        if not self.config.keep_numbers:
            tokens = [t for t in tokens if not t.isdigit()]

        return tokens

    def _split_camel_case(self, text: str) -> str:
        """Insert spaces at camelCase / digit boundaries.

        Splits in four passes so each transformation is independent:
          1. Acronym boundary: ``HTTPServer`` -> ``HTTP Server``
          2. Lower/digit -> upper: ``myValue`` -> ``my Value``
          3. Letter -> digit: ``approveOrder2`` -> ``approveOrder 2``
          4. Digit -> letter: ``v2Server`` -> ``v 2Server``
        """
        text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
        text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
        return text


def build_tokenizer(cfg: TokenizerConfig) -> LabelTokenizer:
    """Build a tokenizer from configuration."""
    return SimpleTokenizer(cfg)


def _extract_labels(ir: IR, profile: LexicalProfile) -> List[Tuple[Optional[str], str, str]]:
    """Extract label candidates from IR according to profile.

    Thin adapter over :func:`cmbenchmark.measures.labels.iter_labels` that preserves
    the historical ``(label_text, element_type, element_id)`` shape expected by the
    rest of this module. Nested children (UML/Ecore attributes, operations,
    enum literals) are surfaced when ``profile.include_nested_labels`` is set.

    ``label_text`` is ``None`` when the label slot exists but holds no string
    value, so downstream "missing label" counters can distinguish a missing
    name from an absent slot.
    """
    out: List[Tuple[Optional[str], str, str]] = []
    for view in iter_labels(
        ir,
        include_nodes=profile.include_nodes,
        include_edges=profile.include_edges,
        include_nested_labels=profile.include_nested_labels,
        label_attributes=profile.label_attributes,
    ):
        text: Optional[str] = view.name if view.name else None
        out.append((text, view.type, view.id))
    return out


def _detect_case_style(text: str) -> str:
    """Detect the case style of a text label."""
    normalized = text.strip()
    if not normalized:
        return "empty"
    
    # Check for camelCase
    if re.match(r'^[a-z][a-zA-Z0-9]*$', normalized) and any(c.isupper() for c in normalized):
        return "camelCase"
    
    # Check for PascalCase
    if re.match(r'^[A-Z][a-zA-Z0-9]*$', normalized) and any(c.islower() for c in normalized):
        return "PascalCase"

    # Check for UPPER_CASE
    if re.match(r'^[A-Z0-9]+(?:_[A-Z0-9]+)+$', normalized):
        return "UPPER_CASE"
    
    # Check for snake_case
    if re.match(r'^[a-z0-9]+(?:_[a-z0-9]+)+$', normalized):
        return "snake_case"
    
    # Check for kebab-case
    if re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)+$', normalized):
        return "kebab-case"
    
    # Check for lowercase
    if normalized.islower():
        return "lowercase"
    
    # Check for UPPERCASE (no underscores)
    if normalized.isupper() and normalized.isalpha():
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


def _is_d2_m1_label_eligible(elem_type: str) -> bool:
    """Whether a label slot contributes to D2.M1 eligibility.

    Accepts both plain IR types (e.g. ``LiteralString``) and namespaced
    variants (e.g. ``uml:LiteralString``).
    """
    canonical = elem_type.rsplit(":", 1)[-1]
    return canonical not in _D2_M1_EXCLUDED_UML_NODE_TYPES


def compute_lexical_measures(
    ir_models: Iterable[IR],
    lexical_profile: LexicalProfile,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
    total_models: Optional[int] = None,
) -> Tuple[LexicalMeasuresDataset, LexicalMeasuresPerModel]:
    """
    Compute lexical quality measures (D2.M1-D2.M6) for IR models.
    
    Args:
        ir_models: List of IR models to analyze
        lexical_profile: Configuration for lexical measures
        
    Returns:
        Tuple of (dataset_measures, per_model_measures)
    """
    tokenizer = build_tokenizer(lexical_profile.tokenizer)

    # Build language detector (Lingua) once for the whole dataset.
    # We explicitly exclude Latin and Esperanto to reduce false positives.
    detector = None
    try:
        from lingua import Language, LanguageDetectorBuilder  # type: ignore

        detector = (
            LanguageDetectorBuilder.from_all_languages_without(Language.LATIN, Language.ESPERANTO)
            .build()
        )
    except Exception:
        detector = None

    def _lang_to_code(lang_obj: object) -> Optional[str]:
        """Convert Lingua Language enum to an ISO 639-1 lowercase code if possible."""
        if lang_obj is None:
            return None
        # Try ISO 639-1
        iso1 = getattr(lang_obj, "iso_code_639_1", None)
        if iso1 is not None:
            name = getattr(iso1, "name", None)
            if name:
                return str(name).lower()
            s = str(iso1)
            if s:
                return s.lower()
        # Fallback to ISO 639-3 if needed
        iso3 = getattr(lang_obj, "iso_code_639_3", None)
        if iso3 is not None:
            name = getattr(iso3, "name", None)
            if name:
                return str(name).lower()
            s = str(iso3)
            if s:
                return s.lower()
        # Last resort: the enum name (e.g. "ENGLISH")
        n = getattr(lang_obj, "name", None)
        return str(n).lower() if n else None
    
    # Per-model accumulators
    per_model_d2m1: Dict[str, D2M1LabelPresencePerModel] = {}
    per_model_d2m2: Dict[str, D2M2LabelLengthPerModel] = {}
    per_model_d2m3: Dict[str, D2M3NamingConventionPerModel] = {}
    per_model_d2m4: Dict[str, D2M4SingleMultiWordPerModel] = {}
    per_model_d2m5: Dict[str, D2M5LexicalDiversityPerModel] = {}
    per_model_d2m6: Dict[str, D2M6LanguageUsagePerModel] = {}
    
    # Dataset-level accumulators
    dataset_label_eligible_count = 0
    dataset_label_present_count = 0
    label_missing_by_type: Dict[str, int] = {}
    dataset_language_counts: Counter[str] = Counter()
    
    # For D2.M2: collect medians per model
    label_length_chars_medians: List[float] = []
    label_length_tokens_medians: List[float] = []
    short_label_shares: List[float] = []
    long_label_shares: List[float] = []
    
    # For D2.M3: collect entropies per model
    naming_style_entropies: List[float] = []
    dataset_case_style_counts: Counter[str] = Counter()
    
    # For D2.M4: collect shares per model. `total_m4_present_labels` is an
    # M4-local denominator so the M4 dataset share stays correct when M1 is off.
    share_single_word_labels: List[float] = []
    total_single_word_labels = 0
    total_multi_word_labels = 0
    total_m4_present_labels = 0
    
    # For D2.M5: aggregate tokens across all models
    all_tokens: List[str] = []
    label_occurrence_counts: Counter[str] = Counter()
    
    # Process each IR model
    inferred_total_models: Optional[int] = total_models
    if inferred_total_models is None and hasattr(ir_models, "__len__"):
        try:
            inferred_total_models = len(ir_models)  # type: ignore[arg-type]
        except TypeError:
            inferred_total_models = None

    processed_models = 0
    for model_index, ir in enumerate(ir_models, start=1):
        if cancel_requested and cancel_requested():
            raise InterruptedError("Measure computation cancelled.")
        processed_models = model_index

        labels = _extract_labels(ir, lexical_profile)

        # D2.M6: Language Usage (per-model + dataset), both gated by enable_d2_m6.
        # When disabled, per-model language rows remain empty and dataset counts
        # stay empty as well.
        merged_text = " ".join(
            label_text.strip()
            for label_text, _, _ in labels
            if isinstance(label_text, str) and label_text.strip()
        ).strip()
        detected_code = "unknown"
        if detector is not None and merged_text:
            try:
                lang = detector.detect_language_of(merged_text)
                detected_code = _lang_to_code(lang) or "unknown"
            except Exception:
                detected_code = "unknown"
        if lexical_profile.enable_d2_m6:
            per_model_d2m6[ir.id] = D2M6LanguageUsagePerModel(language=detected_code)
            dataset_language_counts[detected_code] += 1

        # D2.M1 has a stricter notion of "label-eligible" than other lexical
        # measures: some UML node kinds are value carriers rather than labelled
        # modelling concepts and must not count as missing labels.
        d2m1_labels = [t for t in labels if _is_d2_m1_label_eligible(t[1])]
        eligible_count = len(d2m1_labels)
        present_count = sum(1 for label_text, _, _ in d2m1_labels if label_text and label_text.strip())
        present_share = present_count / eligible_count if eligible_count > 0 else 0.0
        missing_share = 1.0 - present_share

        missing_by_type: Dict[str, int] = {}
        for label_text, elem_type, _ in d2m1_labels:
            if not label_text or not label_text.strip():
                missing_by_type[elem_type] = missing_by_type.get(elem_type, 0) + 1

        missing_count_by_type = {
            elem_type: count for elem_type, count in missing_by_type.items() if count > 0
        }

        # D2.M1: Label Presence
        if lexical_profile.enable_d2_m1:
            per_model_d2m1[ir.id] = D2M1LabelPresencePerModel(
                label_eligible_count=eligible_count,
                label_present_count=present_count,
                label_present_share=present_share,
                label_missing_share=missing_share,
                label_missing_count_by_type=missing_count_by_type,
            )
            dataset_label_eligible_count += eligible_count
            dataset_label_present_count += present_count
            for elem_type, count in missing_by_type.items():
                label_missing_by_type[elem_type] = label_missing_by_type.get(elem_type, 0) + count

        # D2.M2: Label Length
        present_labels = [(label_text, elem_type) for label_text, elem_type, _ in labels if label_text and label_text.strip()]

        if lexical_profile.enable_d2_m5:
            for label_text, _ in present_labels:
                normalized_label = label_text.strip()
                if normalized_label:
                    label_occurrence_counts[normalized_label] += 1

        if lexical_profile.enable_d2_m2 and present_labels:
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
        elif lexical_profile.enable_d2_m2:
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
        if lexical_profile.enable_d2_m3:
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
        if lexical_profile.enable_d2_m4:
            single_word_count = 0
            multi_word_count = 0

            total_present_labels = len(present_labels)
            for label_text, _ in present_labels:
                tokens = tokenizer.tokenize(label_text)
                if len(tokens) == 1:
                    single_word_count += 1
                elif len(tokens) > 1:
                    multi_word_count += 1

            single_word_share = single_word_count / total_present_labels if total_present_labels > 0 else 0.0
            multi_word_share = multi_word_count / total_present_labels if total_present_labels > 0 else 0.0

            per_model_d2m4[ir.id] = D2M4SingleMultiWordPerModel(
                single_word_label_count=single_word_count,
                multi_word_label_count=multi_word_count,
                single_word_label_share=single_word_share,
                multi_word_label_share=multi_word_share,
            )

            share_single_word_labels.append(single_word_share)
            total_single_word_labels += single_word_count
            total_multi_word_labels += multi_word_count
            total_m4_present_labels += total_present_labels

        # D2.M5: Lexical Diversity
        if lexical_profile.enable_d2_m5:
            model_tokens: List[str] = []
            for label_text, _ in present_labels:
                tokens = tokenizer.tokenize(label_text)
                model_tokens.extend(tokens)
                all_tokens.extend(tokens)

            vocab_size = len(set(model_tokens))
            total_tokens = len(model_tokens)
            ttr = vocab_size / total_tokens if total_tokens > 0 else 0.0

            per_model_d2m5[ir.id] = D2M5LexicalDiversityPerModel(
                total_tokens=total_tokens,
                vocab_size=vocab_size,
                type_token_ratio=ttr,
            )

        if progress_callback and (
            model_index % 5 == 0
            or (
                inferred_total_models is not None
                and model_index == inferred_total_models
            )
        ):
            progress_callback(model_index, inferred_total_models or model_index)

    if (
        progress_callback
        and processed_models > 0
        and processed_models % 5 != 0
        and (
            inferred_total_models is None
            or processed_models != inferred_total_models
        )
    ):
        progress_callback(processed_models, inferred_total_models or processed_models)
    
    # Build dataset-level measures
    dataset_label_present_share = dataset_label_present_count / dataset_label_eligible_count if dataset_label_eligible_count > 0 else 0.0
    dataset_label_missing_share = 1.0 - dataset_label_present_share
    
    label_missing_count_by_type = {
        elem_type: count for elem_type, count in label_missing_by_type.items() if count > 0
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
        score=dataset_label_present_share * 100,
        label_missing_count_by_type=label_missing_count_by_type,
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
    
    dataset_share_single_word = (
        total_single_word_labels / total_m4_present_labels
        if total_m4_present_labels > 0
        else 0.0
    )
    
    d2m4_dataset = D2M4SingleMultiWordDataset(
        total_single_word_labels=total_single_word_labels,
        total_multi_word_labels=total_multi_word_labels,
        dataset_share_single_word_labels=dataset_share_single_word,
        share_single_word_labels_stats=_compute_distribution_summary(share_single_word_labels),
    )
    
    vocab_size = len(set(all_tokens))
    total_tokens = len(all_tokens)
    ttr = vocab_size / total_tokens if total_tokens > 0 else 0.0
    top_labels = label_occurrence_counts.most_common(50)
    top_tokens = Counter(all_tokens).most_common(50)

    d2m5_dataset = D2M5LexicalDiversityDataset(
        total_tokens=total_tokens,
        vocab_size=vocab_size,
        type_token_ratio=ttr,
        top_labels=top_labels,
        top_tokens=top_tokens,
    )

    d2m6_dataset = D2M6LanguageUsageDataset(language_counts=dict(dataset_language_counts))
    
    dataset_measures = LexicalMeasuresDataset(
        d2_m1_label_presence=d2m1_dataset,
        d2_m2_label_length=d2m2_dataset,
        d2_m3_naming_convention=d2m3_dataset,
        d2_m4_single_multi_word=d2m4_dataset,
        d2_m5_lexical_diversity=d2m5_dataset,
        d2_m6_language_usage=d2m6_dataset,
    )
    
    per_model_measures = LexicalMeasuresPerModel(
        d2_m1_label_presence=per_model_d2m1,
        d2_m2_label_length=per_model_d2m2,
        d2_m3_naming_convention=per_model_d2m3,
        d2_m4_single_multi_word=per_model_d2m4,
        d2_m5_lexical_diversity=per_model_d2m5,
        d2_m6_language_usage=per_model_d2m6,
    )
    
    return dataset_measures, per_model_measures
