"""Report-building service.

This module builds a *derived* report JSON payload for the frontend, mirroring the
transformations previously done in `frontend/src/hooks/useReportData.ts`.

The goal is for `/api/report` to return a stable, UI-ready structure (chart
series, histogram bins, top-N tables, etc.) so the frontend can stay "thin".
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


def _get(d: Optional[Mapping[str, Any]], *path: str, default: Any = None) -> Any:
    """Safe nested dict getter."""
    cur: Any = d
    for key in path:
        if not isinstance(cur, Mapping):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def create_histogram_data(values: Sequence[Any], bins: int = 20) -> List[Dict[str, Any]]:
    """Create histogram bins like the TS `createHistogramData` helper."""
    nums = [float(v) for v in values if _is_finite_number(v)]
    if not nums:
        return []
    mn = min(nums)
    mx = max(nums)
    if mn == mx:
        return [{"bin": f"{mn:.0f}", "count": len(nums)}]

    if bins <= 0:
        bins = 20
    bin_width = (mx - mn) / bins
    if bin_width <= 0:
        return [{"bin": f"{mn:.0f}", "count": len(nums)}]

    counts = [0] * bins
    for v in nums:
        idx = int((v - mn) / bin_width)
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    out: List[Dict[str, Any]] = []
    for i, c in enumerate(counts):
        a = mn + i * bin_width
        b = mn + (i + 1) * bin_width
        out.append({"bin": f"{a:.0f}-{b:.0f}", "count": c})
    return out


def create_share_histogram_data(values: Sequence[Any], bins: int = 20) -> List[Dict[str, Any]]:
    """Histogram helper specialized for shares in [0, 1] with percent bins."""
    clamped: List[float] = []
    for v in values:
        if not _is_finite_number(v):
            continue
        fv = float(v)
        fv = max(0.0, min(1.0, fv))
        if math.isfinite(fv):
            clamped.append(fv)
    if not clamped:
        return []

    mn = min(clamped)
    mx = max(clamped)
    if mn == mx:
        p = f"{mn * 100:.1f}"
        return [{"bin": f"{p}-{p}%", "count": len(clamped)}]

    if bins <= 0:
        bins = 20
    bin_width = (mx - mn) / bins
    if bin_width <= 0:
        p = f"{mn * 100:.1f}"
        return [{"bin": f"{p}-{p}%", "count": len(clamped)}]

    counts = [0] * bins
    for v in clamped:
        idx = int((v - mn) / bin_width)
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    decimals = 1 if (mx - mn) < 0.2 else 0
    out: List[Dict[str, Any]] = []
    for i, c in enumerate(counts):
        a = mn + i * bin_width
        b = mn + (i + 1) * bin_width
        fa = f"{a * 100:.{decimals}f}"
        fb = f"{b * 100:.{decimals}f}"
        out.append({"bin": f"{fa}-{fb}%", "count": c})
    return out


def build_report_data(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_info: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a derived report payload for the UI."""
    ir_index = _get(ir_info, "index", default={}) if ir_info else {}
    if not isinstance(ir_index, Mapping):
        ir_index = {}

    # D1.M1 - Parse Status
    parse_status = _get(measures, "parsing", "d1_m1_parse_status")
    if isinstance(parse_status, Mapping):
        parse_status_chart_data = [
            {"name": "Success", "value": int(parse_status.get("n_success", 0) or 0), "share": float(parse_status.get("share_success", 0) or 0)},
            {"name": "Partial", "value": int(parse_status.get("n_partial", 0) or 0), "share": float(parse_status.get("share_partial", 0) or 0)},
            {"name": "Failure", "value": int(parse_status.get("n_failed", 0) or 0), "share": float(parse_status.get("share_failed", 0) or 0)},
        ]
    else:
        parse_status_chart_data = []

    # D1.M2 - Elements & Skips
    d1_m2 = _get(measures_per_model, "parsing", "d1_m2_elements_loaded_skipped", default={})
    if not isinstance(d1_m2, Mapping):
        d1_m2 = {}
    skip_ratios = [v.get("skip_ratio") for v in d1_m2.values() if isinstance(v, Mapping)]
    skip_ratio_histogram = create_histogram_data(skip_ratios)
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

    # D2.M1 - Label Presence
    label_presence = _get(measures, "lexical", "d2_m1_label_presence")
    if isinstance(label_presence, Mapping):
        eligible = int(label_presence.get("dataset_label_eligible_count", 0) or 0)
        present = int(label_presence.get("dataset_label_present_count", 0) or 0)
        label_presence_chart_data = {
            "present": present,
            "missing": eligible - present,
            "presentShare": float(label_presence.get("dataset_label_present_share", 0) or 0),
            "missingShare": float(label_presence.get("dataset_label_missing_share", 0) or 0),
        }
        lm_by_type = label_presence.get("label_missing_share_by_type") or {}
    else:
        label_presence_chart_data = None
        lm_by_type = {}
    if not isinstance(lm_by_type, Mapping):
        lm_by_type = {}
    label_presence_by_type = [{"type": str(t), "missingShare": float(s or 0)} for t, s in lm_by_type.items()]

    # D2.M2 - Label Length
    label_length = _get(measures, "lexical", "d2_m2_label_length")
    d2_m2 = _get(measures_per_model, "lexical", "d2_m2_label_length", default={})
    if not isinstance(d2_m2, Mapping):
        d2_m2 = {}
    label_length_chars_medians = [v.get("label_length_chars_median") for v in d2_m2.values() if isinstance(v, Mapping)]
    label_length_tokens_medians = [v.get("label_length_tokens_median") for v in d2_m2.values() if isinstance(v, Mapping)]
    label_length_chars_histogram = create_histogram_data(label_length_chars_medians)
    label_length_tokens_histogram = create_histogram_data(label_length_tokens_medians)
    label_length_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "charsMedian": float(data.get("label_length_chars_median", 0) or 0),
                    "tokensMedian": float(data.get("label_length_tokens_median", 0) or 0),
                    "shortShare": float(data.get("short_label_share", 0) or 0),
                    "longShare": float(data.get("long_label_share", 0) or 0),
                }
                for model_id, data in d2_m2.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["charsMedian"],
            reverse=True,
        )[:10]
        if d2_m2
        else []
    )

    # D2.M3 - Naming Convention
    naming_convention = _get(measures, "lexical", "d2_m3_naming_convention")
    if isinstance(naming_convention, Mapping):
        counts = naming_convention.get("dataset_case_style_counts") or {}
        shares = naming_convention.get("dataset_case_style_share") or {}
    else:
        counts, shares = {}, {}
    if not isinstance(counts, Mapping):
        counts = {}
    if not isinstance(shares, Mapping):
        shares = {}
    naming_convention_chart_data = [
        {"caseStyle": str(case_style), "count": int(count or 0), "share": float(shares.get(case_style, 0) or 0)}
        for case_style, count in counts.items()
    ]
    d2_m3 = _get(measures_per_model, "lexical", "d2_m3_naming_convention", default={})
    if not isinstance(d2_m3, Mapping):
        d2_m3 = {}
    naming_style_entropies = [
        float(x)
        for x in (v.get("naming_style_entropy") for v in d2_m3.values() if isinstance(v, Mapping))
        if _is_finite_number(x)
    ]
    naming_style_entropy_histogram = create_histogram_data(naming_style_entropies)

    # D2.M4 - Single vs Multi Word
    single_multi_word = _get(measures, "lexical", "d2_m4_single_multi_word")
    if isinstance(single_multi_word, Mapping):
        single = int(single_multi_word.get("total_single_word_labels", 0) or 0)
        multi = int(single_multi_word.get("total_multi_word_labels", 0) or 0)
        single_share = float(single_multi_word.get("dataset_share_single_word_labels", 0) or 0)
        single_multi_word_chart_data = {"single": single, "multi": multi, "singleShare": single_share, "multiShare": 1 - single_share}
    else:
        single_multi_word_chart_data = None
    d2_m4 = _get(measures_per_model, "lexical", "d2_m4_single_multi_word", default={})
    if not isinstance(d2_m4, Mapping):
        d2_m4 = {}
    single_word_shares = [
        float(x)
        for x in (v.get("single_word_label_share") for v in d2_m4.values() if isinstance(v, Mapping))
        if _is_finite_number(x)
    ]
    single_word_share_histogram = create_histogram_data(single_word_shares)

    # D2.M5 - Lexical Diversity
    lexical_diversity = _get(measures, "lexical", "d2_m5_lexical_diversity")
    d2_m5 = _get(measures_per_model, "lexical", "d2_m5_lexical_diversity", default={})
    if not isinstance(d2_m5, Mapping):
        d2_m5 = {}
    lexical_diversity_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "totalTokens": int(data.get("total_tokens", 0) or 0),
                    "vocabSize": int(data.get("vocab_size", 0) or 0),
                    "typeTokenRatio": float(data.get("type_token_ratio", 0) or 0),
                    "stopwordShare": float(data.get("stopword_share", 0) or 0),
                }
                for model_id, data in d2_m5.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["typeTokenRatio"],
            reverse=True,
        )[:10]
        if d2_m5
        else []
    )

    # D3.M1 - Construct Presence
    construct_presence = _get(measures, "constructs", "d3_m1_construct_presence")
    construct_catalog = _get(construct_presence, "construct_catalog", default={})
    if not isinstance(construct_catalog, Mapping):
        construct_catalog = {}
    construct_dimension_score = _get(measures, "constructs", "score", default=None)
    construct_presence_per_model = _get(measures_per_model, "constructs", "d3_m1_construct_presence", default={})
    if not isinstance(construct_presence_per_model, Mapping):
        construct_presence_per_model = {}

    if isinstance(construct_presence, Mapping):
        available = int(construct_presence.get("constructs_available_count", 0) or 0)
        observed = int(construct_presence.get("constructs_observed_count", 0) or 0)
        cov = float(construct_presence.get("coverage_share", 0) or 0)
        construct_presence_chart_data = {"observed": observed, "missing": available - observed, "observedShare": cov, "missingShare": 1 - cov}
    else:
        construct_presence_chart_data = None

    coverage_shares = [v.get("coverage_share") for v in construct_presence_per_model.values() if isinstance(v, Mapping)]
    coverage_share_histogram = create_share_histogram_data(coverage_shares)
    unknown_type_shares = [v.get("unknown_type_share", 0) for v in construct_presence_per_model.values() if isinstance(v, Mapping)]
    unknown_type_share_histogram = create_share_histogram_data(unknown_type_shares)

    construct_presence_per_model_rows: List[Dict[str, Any]] = []
    if construct_presence_per_model:
        for model_id, data in construct_presence_per_model.items():
            if not isinstance(data, Mapping):
                continue
            present_constructs = data.get("present_constructs") or {}
            if not isinstance(present_constructs, Mapping):
                present_constructs = {}
            construct_presence_per_model_rows.append(
                {
                    "modelId": str(model_id),
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "presentConstructs": {str(cid): bool(present) for cid, present in present_constructs.items()},
                }
            )

    coverage_outliers = [
        {
            "modelId": model_id,
            "relpath": str(ir_index.get(model_id) or model_id),
            "coverageShare": float(data.get("coverage_share", 0) or 0),
            "constructsObservedCount": int(data.get("constructs_observed_count", 0) or 0),
            "constructsAvailableCount": int(data.get("constructs_available_count", 0) or 0),
            "unknownTypeShare": float(data.get("unknown_type_share", 0) or 0),
            "unknownNodeTypeCount": int(data.get("unknown_node_type_count", 0) or 0),
            "unknownEdgeTypeCount": int(data.get("unknown_edge_type_count", 0) or 0),
        }
        for model_id, data in construct_presence_per_model.items()
        if isinstance(data, Mapping)
    ]
    lowest_coverage = sorted(coverage_outliers, key=lambda x: x["coverageShare"])[:10]
    highest_coverage = sorted(coverage_outliers, key=lambda x: x["coverageShare"], reverse=True)[:10]

    # Missing constructs
    missing_constructs: List[Dict[str, Any]]
    explicit_missing = _get(construct_presence, "missing_constructs") if isinstance(construct_presence, Mapping) else None
    if isinstance(explicit_missing, list):
        missing_constructs = [
            {
                "constructId": m.get("constructId"),
                "group": m.get("group"),
                "description": m.get("description"),
                "kind": m.get("kind"),
            }
            for m in explicit_missing
            if isinstance(m, Mapping) and m.get("constructId") is not None
        ]
    elif isinstance(construct_presence, Mapping) and construct_presence_per_model:
        all_present: set[str] = set()
        all_constructs: set[str] = set()
        for m in construct_presence_per_model.values():
            if not isinstance(m, Mapping):
                continue
            pc = m.get("present_constructs") or {}
            if not isinstance(pc, Mapping):
                continue
            for cid, present in pc.items():
                all_constructs.add(str(cid))
                if bool(present):
                    all_present.add(str(cid))
        missing = [cid for cid in all_constructs if cid not in all_present]
        missing_constructs = [{"constructId": cid} for cid in missing]
    else:
        missing_constructs = []

    # Unknown types
    unknown_types: List[Dict[str, Any]]
    utd = _get(construct_presence, "unknown_type_examples_dataset") if isinstance(construct_presence, Mapping) else None
    if isinstance(utd, Mapping):
        unknown_types = sorted(
            [{"type": str(t), "count": int(c or 0)} for t, c in utd.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:25]
    elif construct_presence_per_model:
        type_counts: Dict[str, int] = {}
        for m in construct_presence_per_model.values():
            if not isinstance(m, Mapping):
                continue
            examples = m.get("unknown_type_examples") or {}
            if not isinstance(examples, Mapping):
                continue
            for t, c in examples.items():
                type_counts[str(t)] = type_counts.get(str(t), 0) + int(c or 0)
        unknown_types = sorted(
            [{"type": t, "count": c} for t, c in type_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]
    else:
        unknown_types = []

    coverage_by_group_raw = _get(construct_presence, "coverage_by_group", default={})
    if not isinstance(coverage_by_group_raw, Mapping):
        coverage_by_group_raw = {}
    coverage_by_group = sorted(
        [
            {
                "group": str(group),
                "available": int((stats or {}).get("available", 0) or 0) if isinstance(stats, Mapping) else 0,
                "observed": int((stats or {}).get("observed", 0) or 0) if isinstance(stats, Mapping) else 0,
                "missing": int((stats or {}).get("missing", 0) or 0) if isinstance(stats, Mapping) else 0,
                "coverageShare": float((stats or {}).get("coverage_share", 0) or 0) if isinstance(stats, Mapping) else 0.0,
            }
            for group, stats in coverage_by_group_raw.items()
        ],
        key=lambda x: x["coverageShare"],
    )

    coverage_by_kind_raw = _get(construct_presence, "coverage_by_kind", default={})
    if not isinstance(coverage_by_kind_raw, Mapping):
        coverage_by_kind_raw = {}
    coverage_by_kind = sorted(
        [
            {
                "kind": str(kind),
                "available": int((stats or {}).get("available", 0) or 0) if isinstance(stats, Mapping) else 0,
                "observed": int((stats or {}).get("observed", 0) or 0) if isinstance(stats, Mapping) else 0,
                "missing": int((stats or {}).get("missing", 0) or 0) if isinstance(stats, Mapping) else 0,
                "coverageShare": float((stats or {}).get("coverage_share", 0) or 0) if isinstance(stats, Mapping) else 0.0,
            }
            for kind, stats in coverage_by_kind_raw.items()
        ],
        key=lambda x: x["coverageShare"],
    )

    # D3.M3 - Construct Frequency
    construct_frequency = _get(measures, "constructs", "d3_m3_construct_frequency")
    dataset_count_by_construct = _get(construct_frequency, "dataset_count_by_construct", default={})
    if not isinstance(dataset_count_by_construct, Mapping):
        dataset_count_by_construct = {}
    dataset_relative_frequency_by_construct = _get(
        construct_frequency, "dataset_relative_frequency_by_construct", default={}
    )
    if not isinstance(dataset_relative_frequency_by_construct, Mapping):
        dataset_relative_frequency_by_construct = {}
    dataset_total_construct_instances = int(
        _get(construct_frequency, "dataset_total_construct_instances", default=0) or 0
    )

    construct_frequency_data = sorted(
        [
            {
                "constructId": str(cid),
                "count": int(count or 0),
                "share": float(dataset_relative_frequency_by_construct.get(str(cid), 0.0) or 0.0),
                "group": _get(construct_catalog, str(cid), "group"),
                "description": _get(construct_catalog, str(cid), "description"),
                "kind": _get(construct_catalog, str(cid), "kind"),
            }
            for cid, count in dataset_count_by_construct.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )
    total_construct_count = dataset_total_construct_instances or sum(
        int(d.get("count", 0) or 0) for d in construct_frequency_data
    )
    if total_construct_count > 0:
        for d in construct_frequency_data:
            if not _is_finite_number(d.get("share")) or float(d.get("share", 0) or 0) <= 0:
                d["share"] = (int(d.get("count", 0) or 0)) / total_construct_count

    cumulative = 0.0
    construct_frequency_pareto: List[Dict[str, Any]] = []
    for idx, d in enumerate(construct_frequency_data):
        cumulative += float(d.get("share", 0.0) or 0.0)
        construct_frequency_pareto.append(
            {
                "rank": idx + 1,
                "constructId": d.get("constructId"),
                "count": d.get("count"),
                "share": d.get("share"),
                "cumulativeShare": cumulative,
            }
        )

    by_group: Dict[str, int] = {}
    for d in construct_frequency_data:
        group = d.get("group") or "—"
        by_group[str(group)] = by_group.get(str(group), 0) + int(d.get("count", 0) or 0)
    total_by_group = sum(by_group.values())
    construct_frequency_by_group = sorted(
        [
            {"group": g, "count": c, "share": (c / total_by_group) if total_by_group > 0 else 0.0}
            for g, c in by_group.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    construct_frequency_per_model = _get(
        measures_per_model, "constructs", "d3_m3_construct_frequency", default={}
    )
    if not isinstance(construct_frequency_per_model, Mapping):
        construct_frequency_per_model = {}
    construct_frequency_per_model_rows: List[Dict[str, Any]] = []
    construct_frequency_per_model_shares: List[Dict[str, Any]] = []
    construct_frequency_totals: List[Dict[str, Any]] = []
    for model_id, data in construct_frequency_per_model.items():
        if not isinstance(data, Mapping):
            continue
        counts = data.get("count_by_construct") or {}
        if not isinstance(counts, Mapping):
            counts = {}
        shares = data.get("relative_frequency_by_construct") or {}
        if not isinstance(shares, Mapping):
            shares = {}
        total_instances = int(data.get("total_construct_instances", 0) or 0)
        utilization_entropy = float(data.get("utilization_entropy", 0) or 0)
        construct_frequency_per_model_rows.append(
            {
                "modelId": str(model_id),
                "relpath": str(ir_index.get(model_id) or model_id),
                "countsByConstruct": {str(cid): int(c or 0) for cid, c in counts.items() if int(c or 0) > 0},
            }
        )
        construct_frequency_per_model_shares.append(
            {
                "modelId": str(model_id),
                "relpath": str(ir_index.get(model_id) or model_id),
                "sharesByConstruct": {
                    str(cid): float(s or 0) for cid, s in shares.items() if float(s or 0) > 0
                },
                "totalConstructInstances": total_instances,
                "utilizationEntropy": utilization_entropy,
            }
        )
        construct_frequency_totals.append(
            {
                "modelId": str(model_id),
                "relpath": str(ir_index.get(model_id) or model_id),
                "totalConstructInstances": total_instances,
                "utilizationEntropy": utilization_entropy,
            }
        )

    total_construct_instances_per_model = [
        v.get("totalConstructInstances")
        for v in construct_frequency_totals
        if _is_finite_number(v.get("totalConstructInstances"))
    ]
    utilization_entropies = [
        v.get("utilizationEntropy")
        for v in construct_frequency_totals
        if _is_finite_number(v.get("utilizationEntropy"))
    ]
    construct_frequency_total_histogram = create_histogram_data(total_construct_instances_per_model)
    construct_frequency_entropy_histogram = create_share_histogram_data(utilization_entropies)
    construct_frequency_top_models = (
        sorted(
            construct_frequency_totals,
            key=lambda x: x.get("totalConstructInstances", 0) or 0,
            reverse=True,
        )[:10]
        if construct_frequency_totals
        else []
    )

    return {
        # Parsing measures
        "parseStatus": parse_status,
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
        # Lexical measures
        "labelPresence": label_presence,
        "labelPresenceChartData": label_presence_chart_data,
        "labelPresenceByType": label_presence_by_type,
        "labelLength": label_length,
        "labelLengthCharsHistogram": label_length_chars_histogram,
        "labelLengthTokensHistogram": label_length_tokens_histogram,
        "labelLengthTop10": label_length_top10,
        "namingConvention": naming_convention,
        "namingConventionChartData": naming_convention_chart_data,
        "namingStyleEntropies": naming_style_entropies,
        "namingStyleEntropyHistogram": naming_style_entropy_histogram,
        "singleMultiWord": single_multi_word,
        "singleMultiWordChartData": single_multi_word_chart_data,
        "singleWordShares": single_word_shares,
        "singleWordShareHistogram": single_word_share_histogram,
        "lexicalDiversity": lexical_diversity,
        "lexicalDiversityTop10": lexical_diversity_top10,
        # Construct measures
        "constructPresence": construct_presence,
        "constructDimensionScore": construct_dimension_score,
        "constructCatalog": dict(construct_catalog),
        "constructPresenceChartData": construct_presence_chart_data,
        "constructPresencePerModel": construct_presence_per_model_rows,
        "coverageShareHistogram": coverage_share_histogram,
        "unknownTypeShareHistogram": unknown_type_share_histogram,
        "lowestCoverage": lowest_coverage,
        "highestCoverage": highest_coverage,
        "missingConstructs": missing_constructs,
        "unknownTypes": unknown_types,
        "coverageByGroup": coverage_by_group,
        "coverageByKind": coverage_by_kind,
        "constructFrequency": construct_frequency,
        "constructFrequencyData": construct_frequency_data,
        "constructFrequencyPareto": construct_frequency_pareto,
        "constructFrequencyByGroup": construct_frequency_by_group,
        "constructFrequencyPerModel": construct_frequency_per_model_rows,
        "constructFrequencyTotalsHistogram": construct_frequency_total_histogram,
        "constructFrequencyEntropyHistogram": construct_frequency_entropy_histogram,
        "constructFrequencyTopModels": construct_frequency_top_models,
        "constructFrequencyPerModelShares": construct_frequency_per_model_shares,
    }
