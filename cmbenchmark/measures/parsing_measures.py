"""Computation functions for parsing-related measures."""

import statistics
from typing import Dict, List, Tuple
from cmbenchmark.types.dataset import IRInfo
from cmbenchmark.types.parsing import ModelParseDiagnostics
from cmbenchmark.types.measures import (
    DistributionSummary,
    D1M1ParseStatusResult,
    D1M2ElementsLoadedSkippedResult,
    D1M3ParsingTimeResult,
    D1M4FileSizeResult,
    D1M5WarningsResult,
    D1M1ParseStatusPerModel,
    D1M2ElementsLoadedSkippedPerModel,
    D1M3ParsingTimePerModel,
    D1M4FileSizePerModel,
    D1M5WarningsPerModel,
    ParsingMeasuresDataset,
    ParsingMeasuresPerModel,
)


def _compute_percentile(values: List[float], percentile: float) -> float:
    """Compute a percentile value from a list of numbers."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = percentile / 100.0 * (len(sorted_values) - 1)
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def _compute_distribution_summary(values: List[float]) -> DistributionSummary:
    """Compute statistical summary for a list of values as DistributionSummary."""
    if not values:
        return DistributionSummary(
            n=0,
            min=0.0,
            p25=0.0,
            median=0.0,
            mean=0.0,
            p75=0.0,
            max=0.0,
            std=0.0,
        )
    
    return DistributionSummary(
        n=len(values),
        min=min(values),
        p25=_compute_percentile(values, 25),
        median=statistics.median(values),
        mean=statistics.mean(values),
        p75=_compute_percentile(values, 75),
        max=max(values),
        std=statistics.stdev(values) if len(values) > 1 else 0.0,
    )


def compute_d1_m1_parse_status(ir_info: IRInfo) -> Tuple[D1M1ParseStatusResult, Dict[str, D1M1ParseStatusPerModel]]:
    """
    Compute D1.M1 — Parse Status measure.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_result, per_model_dict)
    """
    diagnostics = ir_info.modelParseDiagnostics
    n_models = len(diagnostics)
    
    if n_models == 0:
        dataset_result = D1M1ParseStatusResult(
            n_models=0,
            n_success=0,
            n_partial=0,
            n_failed=0,
            share_success=0.0,
            share_partial=0.0,
            share_failed=0.0,
            parsing_robustness_index=0.0,
        )
        return dataset_result, {}
    
    n_success = sum(1 for d in diagnostics.values() if d.parse_status == "success")
    n_partial = sum(1 for d in diagnostics.values() if d.parse_status == "warning")
    n_failed = sum(1 for d in diagnostics.values() if d.parse_status == "failure")
    
    share_success = n_success / n_models
    share_partial = n_partial / n_models
    share_failed = n_failed / n_models
    
    # Parsing robustness index: (success + 0.5 * partial) / total
    parsing_robustness_index = (n_success + 0.5 * n_partial) / n_models
    
    dataset_result = D1M1ParseStatusResult(
        n_models=n_models,
        n_success=n_success,
        n_partial=n_partial,
        n_failed=n_failed,
        share_success=share_success,
        share_partial=share_partial,
        share_failed=share_failed,
        parsing_robustness_index=parsing_robustness_index,
    )
    
    # Per-model values
    per_model: Dict[str, D1M1ParseStatusPerModel] = {}
    for model_id, d in diagnostics.items():
        per_model[model_id] = D1M1ParseStatusPerModel(
            parse_status=d.parse_status,
            parse_error_msg=d.parse_error_msg,
        )
    
    return dataset_result, per_model


def compute_d1_m2_elements_loaded_skipped(ir_info: IRInfo) -> Tuple[D1M2ElementsLoadedSkippedResult, Dict[str, D1M2ElementsLoadedSkippedPerModel]]:
    """
    Compute D1.M2 — Elements Loaded vs. Skipped measure.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_result, per_model_dict)
    """
    diagnostics = ir_info.modelParseDiagnostics
    
    total_elements_loaded = sum(d.elements_loaded for d in diagnostics.values())
    total_elements_skipped = sum(d.elements_skipped for d in diagnostics.values())
    
    total_elements = total_elements_loaded + total_elements_skipped
    dataset_skip_ratio = total_elements_skipped / total_elements if total_elements > 0 else 0.0
    
    # Compute skip ratios per model
    skip_ratios = [d.skip_ratio for d in diagnostics.values()]
    skip_ratio_stats = _compute_distribution_summary(skip_ratios)
    
    n_models_with_skips = sum(1 for d in diagnostics.values() if d.elements_skipped > 0)
    share_models_with_skips = n_models_with_skips / len(diagnostics) if diagnostics else 0.0
    
    dataset_result = D1M2ElementsLoadedSkippedResult(
        total_elements_loaded=total_elements_loaded,
        total_elements_skipped=total_elements_skipped,
        dataset_skip_ratio=dataset_skip_ratio,
        skip_ratio_stats=skip_ratio_stats,
        n_models_with_skips=n_models_with_skips,
        share_models_with_skips=share_models_with_skips,
    )
    
    # Per-model values
    per_model: Dict[str, D1M2ElementsLoadedSkippedPerModel] = {}
    for model_id, d in diagnostics.items():
        per_model[model_id] = D1M2ElementsLoadedSkippedPerModel(
            elements_loaded=d.elements_loaded,
            elements_skipped=d.elements_skipped,
            skip_ratio=d.skip_ratio,
        )
    
    return dataset_result, per_model


def compute_d1_m3_parsing_time(ir_info: IRInfo) -> Tuple[D1M3ParsingTimeResult, Dict[str, D1M3ParsingTimePerModel]]:
    """
    Compute D1.M3 — Parsing Time measure.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_result, per_model_dict)
    """
    diagnostics = ir_info.modelParseDiagnostics
    
    parse_times = [float(d.parse_time_ms) for d in diagnostics.values()]
    parse_time_stats = _compute_distribution_summary(parse_times)
    
    parse_time_total_ms = sum(d.parse_time_ms for d in diagnostics.values())
    
    dataset_result = D1M3ParsingTimeResult(
        parse_time_stats=parse_time_stats,
        parse_time_total_ms=parse_time_total_ms,
    )
    
    # Per-model values
    per_model: Dict[str, D1M3ParsingTimePerModel] = {}
    for model_id, d in diagnostics.items():
        per_model[model_id] = D1M3ParsingTimePerModel(
            parse_time_ms=d.parse_time_ms,
        )
    
    return dataset_result, per_model


def compute_d1_m4_file_size(ir_info: IRInfo) -> Tuple[D1M4FileSizeResult, Dict[str, D1M4FileSizePerModel]]:
    """
    Compute D1.M4 — File Size measure.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_result, per_model_dict)
    """
    diagnostics = ir_info.modelParseDiagnostics
    
    source_sizes = [float(d.file_size_bytes_source) for d in diagnostics.values()]
    ir_sizes = [float(d.file_size_bytes_ir) for d in diagnostics.values()]
    
    file_size_source_stats = _compute_distribution_summary(source_sizes)
    file_size_ir_stats = _compute_distribution_summary(ir_sizes)
    
    dataset_result = D1M4FileSizeResult(
        file_size_source_stats=file_size_source_stats,
        file_size_ir_stats=file_size_ir_stats,
    )
    
    # Per-model values
    per_model: Dict[str, D1M4FileSizePerModel] = {}
    for model_id, d in diagnostics.items():
        per_model[model_id] = D1M4FileSizePerModel(
            file_size_bytes_source=d.file_size_bytes_source,
            file_size_bytes_ir=d.file_size_bytes_ir,
        )
    
    return dataset_result, per_model


def compute_d1_m5_warnings(ir_info: IRInfo) -> Tuple[D1M5WarningsResult, Dict[str, D1M5WarningsPerModel]]:
    """
    Compute D1.M5 — Warnings measure.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_result, per_model_dict)
    """
    diagnostics = ir_info.modelParseDiagnostics
    
    n_models_with_warnings = sum(1 for d in diagnostics.values() if d.warning_count > 0)
    share_models_with_warnings = n_models_with_warnings / len(diagnostics) if diagnostics else 0.0
    
    warning_counts = [float(d.warning_count) for d in diagnostics.values()]
    warning_count_stats = _compute_distribution_summary(warning_counts)
    
    warnings_per_element = [d.warnings_per_element for d in diagnostics.values()]
    warnings_per_element_stats = _compute_distribution_summary(warnings_per_element)
    
    # Aggregate warnings by type
    total_warnings_by_type: Dict[str, int] = {}
    n_models_with_warning_type: Dict[str, int] = {}
    
    for d in diagnostics.values():
        for warning_type, count in d.warnings_by_type.items():
            total_warnings_by_type[warning_type] = total_warnings_by_type.get(warning_type, 0) + count
            if count > 0:
                n_models_with_warning_type[warning_type] = n_models_with_warning_type.get(warning_type, 0) + 1
    
    share_models_with_warning_type = {
        warning_type: count / len(diagnostics) if diagnostics else 0.0
        for warning_type, count in n_models_with_warning_type.items()
    }
    
    dataset_result = D1M5WarningsResult(
        n_models_with_warnings=n_models_with_warnings,
        share_models_with_warnings=share_models_with_warnings,
        warning_count_stats=warning_count_stats,
        warnings_per_element_stats=warnings_per_element_stats,
        total_warnings_by_type=total_warnings_by_type,
        n_models_with_warning_type=n_models_with_warning_type,
        share_models_with_warning_type=share_models_with_warning_type,
    )
    
    # Per-model values
    per_model: Dict[str, D1M5WarningsPerModel] = {}
    for model_id, d in diagnostics.items():
        per_model[model_id] = D1M5WarningsPerModel(
            warning_count=d.warning_count,
            warnings_by_type=d.warnings_by_type.copy(),
            warnings_per_element=d.warnings_per_element,
        )
    
    return dataset_result, per_model


def compute_parsing_measures(ir_info: IRInfo) -> Tuple[ParsingMeasuresDataset, ParsingMeasuresPerModel]:
    """
    Compute all parsing-related measures from IRInfo.
    
    Args:
        ir_info: IRInfo object containing parse diagnostics
        
    Returns:
        Tuple of (dataset_measures, per_model_measures)
    """
    d1_m1_dataset, d1_m1_per_model = compute_d1_m1_parse_status(ir_info)
    d1_m2_dataset, d1_m2_per_model = compute_d1_m2_elements_loaded_skipped(ir_info)
    d1_m3_dataset, d1_m3_per_model = compute_d1_m3_parsing_time(ir_info)
    d1_m4_dataset, d1_m4_per_model = compute_d1_m4_file_size(ir_info)
    d1_m5_dataset, d1_m5_per_model = compute_d1_m5_warnings(ir_info)
    
    dataset_measures = ParsingMeasuresDataset(
        d1_m1_parse_status=d1_m1_dataset,
        d1_m2_elements_loaded_skipped=d1_m2_dataset,
        d1_m3_parsing_time=d1_m3_dataset,
        d1_m4_file_size=d1_m4_dataset,
        d1_m5_warnings=d1_m5_dataset,
    )
    
    per_model_measures = ParsingMeasuresPerModel(
        d1_m1_parse_status=d1_m1_per_model,
        d1_m2_elements_loaded_skipped=d1_m2_per_model,
        d1_m3_parsing_time=d1_m3_per_model,
        d1_m4_file_size=d1_m4_per_model,
        d1_m5_warnings=d1_m5_per_model,
    )
    
    return dataset_measures, per_model_measures
