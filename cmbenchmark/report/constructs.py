from __future__ import annotations

from typing import Any, Dict, List, Mapping

from cmbenchmark.report.utils import _get, _is_finite_number, create_histogram_data, create_share_histogram_data


def build_constructs_report(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build derived constructs report fields (D3.*)."""

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
        construct_presence_chart_data = {
            "observed": observed,
            "missing": available - observed,
            "observedShare": cov,
            "missingShare": 1 - cov,
        }
    else:
        construct_presence_chart_data = None

    coverage_shares = [
        v.get("coverage_share") for v in construct_presence_per_model.values() if isinstance(v, Mapping)
    ]
    coverage_share_histogram = create_share_histogram_data(coverage_shares)
    unknown_type_shares = [
        v.get("unknown_type_share", 0) for v in construct_presence_per_model.values() if isinstance(v, Mapping)
    ]
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
    dataset_relative_frequency_by_construct = _get(construct_frequency, "dataset_relative_frequency_by_construct", default={})
    if not isinstance(dataset_relative_frequency_by_construct, Mapping):
        dataset_relative_frequency_by_construct = {}
    dataset_total_construct_instances = int(_get(construct_frequency, "dataset_total_construct_instances", default=0) or 0)

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
    total_construct_count = dataset_total_construct_instances or sum(int(d.get("count", 0) or 0) for d in construct_frequency_data)
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
        [{"group": g, "count": c, "share": (c / total_by_group) if total_by_group > 0 else 0.0} for g, c in by_group.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    construct_frequency_per_model = _get(measures_per_model, "constructs", "d3_m3_construct_frequency", default={})
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
                "sharesByConstruct": {str(cid): float(s or 0) for cid, s in shares.items() if float(s or 0) > 0},
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
        v.get("totalConstructInstances") for v in construct_frequency_totals if _is_finite_number(v.get("totalConstructInstances"))
    ]
    utilization_entropies = [
        v.get("utilizationEntropy") for v in construct_frequency_totals if _is_finite_number(v.get("utilizationEntropy"))
    ]
    construct_frequency_total_histogram = create_histogram_data(total_construct_instances_per_model)
    construct_frequency_entropy_histogram = create_share_histogram_data(utilization_entropies)
    construct_frequency_top_models = (
        sorted(construct_frequency_totals, key=lambda x: x.get("totalConstructInstances", 0) or 0, reverse=True)[:10]
        if construct_frequency_totals
        else []
    )

    return {
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

