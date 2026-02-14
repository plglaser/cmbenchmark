from __future__ import annotations

from typing import Any, Dict, List, Mapping

from cmbenchmark.report.utils import _get, _is_finite_number, create_histogram_data


def build_parsing_report(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build derived parsing report fields (D1.*)."""

    # D1.M1 - Parse Status
    parse_status = _get(measures, "parsing", "d1_m1_parse_status")
    if isinstance(parse_status, Mapping):
        parse_status_chart_data = [
            {
                "name": "Success",
                "value": int(parse_status.get("n_success", 0) or 0),
                "share": float(parse_status.get("share_success", 0) or 0),
            },
            {
                "name": "Partial",
                "value": int(parse_status.get("n_partial", 0) or 0),
                "share": float(parse_status.get("share_partial", 0) or 0),
            },
            {
                "name": "Failure",
                "value": int(parse_status.get("n_failed", 0) or 0),
                "share": float(parse_status.get("share_failed", 0) or 0),
            },
        ]
    else:
        parse_status_chart_data = []

    # D1.M2 - Elements & Skips
    parse_elements_skips = _get(measures, "parsing", "d1_m2_elements_loaded_skipped")
    d1_m2 = _get(measures_per_model, "parsing", "d1_m2_elements_loaded_skipped", default={})
    if not isinstance(d1_m2, Mapping):
        d1_m2 = {}
    skip_ratios = [v.get("skip_ratio") for v in d1_m2.values() if isinstance(v, Mapping)]
    skip_ratio_histogram = create_histogram_data(skip_ratios)
    total_models_evaluated = len(d1_m2)
    models_with_skips = sum(
        1
        for data in d1_m2.values()
        if isinstance(data, Mapping) and int(data.get("elements_skipped", 0) or 0) > 0
    )
    if isinstance(parse_elements_skips, Mapping):
        models_with_skips = int(parse_elements_skips.get("n_models_with_skips", models_with_skips) or 0)
    models_without_skips = max(0, total_models_evaluated - models_with_skips)
    models_with_skips_share = (
        float(parse_elements_skips.get("share_models_with_skips", 0) or 0)
        if isinstance(parse_elements_skips, Mapping)
        else (models_with_skips / total_models_evaluated if total_models_evaluated > 0 else 0.0)
    )

    total_elements_loaded = (
        int(parse_elements_skips.get("total_elements_loaded", 0) or 0)
        if isinstance(parse_elements_skips, Mapping)
        else 0
    )
    total_elements_skipped = (
        int(parse_elements_skips.get("total_elements_skipped", 0) or 0)
        if isinstance(parse_elements_skips, Mapping)
        else 0
    )
    total_elements_processed = total_elements_loaded + total_elements_skipped
    dataset_skip_ratio = (
        float(parse_elements_skips.get("dataset_skip_ratio", 0) or 0)
        if isinstance(parse_elements_skips, Mapping)
        else 0.0
    )
    dataset_load_ratio = max(0.0, min(1.0, 1.0 - dataset_skip_ratio))
    skip_ratio_stats = parse_elements_skips.get("skip_ratio_stats", {}) if isinstance(parse_elements_skips, Mapping) else {}
    if not isinstance(skip_ratio_stats, Mapping):
        skip_ratio_stats = {}
    parse_elements_skips_summary = {
        "totalModelsEvaluated": total_models_evaluated,
        "modelsWithSkips": models_with_skips,
        "modelsWithoutSkips": models_without_skips,
        "modelsWithSkipsShare": models_with_skips_share,
        "totalElementsLoaded": total_elements_loaded,
        "totalElementsSkipped": total_elements_skipped,
        "totalElementsProcessed": total_elements_processed,
        "datasetSkipRatio": dataset_skip_ratio,
        "datasetLoadRatio": dataset_load_ratio,
        "avgSkipRatio": float(skip_ratio_stats.get("mean", 0) or 0),
        "medianSkipRatio": float(skip_ratio_stats.get("median", 0) or 0),
    }
    skip_ratio_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "skipRatio": float(data.get("skip_ratio", 0) or 0),
                    "elementsLoaded": int(data.get("elements_loaded", 0) or 0),
                    "elementsSkipped": int(data.get("elements_skipped", 0) or 0),
                    "relpath": str(ir_index.get(model_id) or model_id),
                }
                for model_id, data in d1_m2.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["skipRatio"],
            reverse=True,
        )[:10]
        if d1_m2
        else []
    )

    # D1.M3 - Parsing Time
    d1_m3 = _get(measures_per_model, "parsing", "d1_m3_parsing_time", default={})
    if not isinstance(d1_m3, Mapping):
        d1_m3 = {}
    parse_times = [v.get("parse_time_ms") for v in d1_m3.values() if isinstance(v, Mapping)]
    parse_time_histogram = create_histogram_data(parse_times)

    # D1.M4 - File Sizes (used for parse scatter + file size plots/tables)
    d1_m4 = _get(measures_per_model, "parsing", "d1_m4_file_size", default={})
    if not isinstance(d1_m4, Mapping):
        d1_m4 = {}
    parse_time_scatter_data: List[Dict[str, Any]] = []
    if d1_m3 and d1_m4:
        for model_id in d1_m3.keys():
            t = d1_m3.get(model_id)
            s = d1_m4.get(model_id)
            if not isinstance(t, Mapping) or not isinstance(s, Mapping):
                continue
            file_size = int(s.get("file_size_bytes_source", 0) or 0)
            parse_time = int(t.get("parse_time_ms", 0) or 0)
            if file_size > 0 and parse_time > 0:
                parse_time_scatter_data.append({"fileSize": file_size, "parseTime": parse_time})

    source_sizes = [v.get("file_size_bytes_source") for v in d1_m4.values() if isinstance(v, Mapping)]
    ir_sizes = [v.get("file_size_bytes_ir") for v in d1_m4.values() if isinstance(v, Mapping)]
    source_size_histogram = create_histogram_data(source_sizes)
    ir_size_histogram = create_histogram_data(ir_sizes)

    file_size_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "sourceSize": int(data.get("file_size_bytes_source", 0) or 0),
                    "irSize": int(data.get("file_size_bytes_ir", 0) or 0),
                    "relpath": str(ir_index.get(model_id) or model_id),
                }
                for model_id, data in d1_m4.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["sourceSize"],
            reverse=True,
        )[:10]
        if d1_m4
        else []
    )
    file_size_bottom10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "sourceSize": int(data.get("file_size_bytes_source", 0) or 0),
                    "irSize": int(data.get("file_size_bytes_ir", 0) or 0),
                    "relpath": str(ir_index.get(model_id) or model_id),
                }
                for model_id, data in d1_m4.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["sourceSize"],
        )[:10]
        if d1_m4
        else []
    )

    # D1.M5 - Warnings
    parse_warnings = _get(measures, "parsing", "d1_m5_warnings")
    warnings_by_type = _get(measures, "parsing", "d1_m5_warnings", "total_warnings_by_type", default={})
    if not isinstance(warnings_by_type, Mapping):
        warnings_by_type = {}
    warnings_chart_data = [{"type": str(t), "count": int(c or 0)} for t, c in warnings_by_type.items()]

    d1_m5 = _get(measures_per_model, "parsing", "d1_m5_warnings", default={})
    if not isinstance(d1_m5, Mapping):
        d1_m5 = {}
    models_with_warnings = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "warningCount": int(data.get("warning_count", 0) or 0),
                    "warningsByType": (
                        {str(k): int(v or 0) for k, v in (data.get("warnings_by_type") or {}).items()}
                        if isinstance(data.get("warnings_by_type") or {}, Mapping)
                        else {}
                    ),
                    "relpath": str(ir_index.get(model_id) or model_id),
                }
                for model_id, data in d1_m5.items()
                if isinstance(data, Mapping) and int(data.get("warning_count", 0) or 0) > 0
            ],
            key=lambda x: x["warningCount"],
            reverse=True,
        )[:10]
        if d1_m5
        else []
    )

    # D1 Parsing dimension score (D1.M1, D1.M2, D1.M5)
    parsing_dimension_score = None
    score_values: List[float] = []
    for measure_obj in (parse_status, parse_elements_skips, parse_warnings):
        if isinstance(measure_obj, Mapping):
            score_value = measure_obj.get("score")
            if _is_finite_number(score_value):
                score_values.append(float(score_value))
    if len(score_values) == 3:
        parsing_dimension_score = sum(score_values) / 3.0

    return {
        "parseStatus": parse_status,
        "parseElementsSkips": parse_elements_skips,
        "parseElementsSkipsSummary": parse_elements_skips_summary,
        "parseWarnings": parse_warnings,
        "parsingDimensionScore": parsing_dimension_score,
        "parseStatusChartData": parse_status_chart_data,
        "skipRatioHistogram": skip_ratio_histogram,
        "skipRatioTop10": skip_ratio_top10,
        "parseTimeHistogram": parse_time_histogram,
        "parseTimeScatterData": parse_time_scatter_data,
        "sourceSizeHistogram": source_size_histogram,
        "irSizeHistogram": ir_size_histogram,
        "fileSizeTop10": file_size_top10,
        "fileSizeBottom10": file_size_bottom10,
        "warningsChartData": warnings_chart_data,
        "modelsWithWarnings": models_with_warnings,
    }
