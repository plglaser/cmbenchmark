from __future__ import annotations

from typing import Any, Dict, Mapping

from cmbenchmark.report.utils import _get, create_histogram_data, create_share_histogram_data


def build_size_report(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build derived size & complexity report fields (D4.*)."""

    # D4.M1 - Model Size
    model_size = _get(measures, "size_complexity", "d4_m1_model_size")
    d4_m1 = _get(measures_per_model, "size_complexity", "d4_m1_model_size", default={})
    if not isinstance(d4_m1, Mapping):
        d4_m1 = {}
    model_size_node_histogram = create_histogram_data([v.get("node_count") for v in d4_m1.values() if isinstance(v, Mapping)])
    model_size_edge_histogram = create_histogram_data([v.get("edge_count") for v in d4_m1.values() if isinstance(v, Mapping)])
    model_size_element_histogram = create_histogram_data([v.get("element_count") for v in d4_m1.values() if isinstance(v, Mapping)])
    model_size_ratio_histogram = create_histogram_data([v.get("edge_node_ratio") for v in d4_m1.values() if isinstance(v, Mapping)])
    model_size_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "nodeCount": int(data.get("node_count", 0) or 0),
                    "edgeCount": int(data.get("edge_count", 0) or 0),
                    "elementCount": int(data.get("element_count", 0) or 0),
                    "edgeNodeRatio": float(data.get("edge_node_ratio", 0) or 0),
                }
                for model_id, data in d4_m1.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["elementCount"],
            reverse=True,
        )[:10]
        if d4_m1
        else []
    )
    model_size_scatter_data = [
        {
            "modelId": model_id,
            "relpath": str(ir_index.get(model_id) or model_id),
            "nodeCount": int(data.get("node_count", 0) or 0),
            "edgeCount": int(data.get("edge_count", 0) or 0),
        }
        for model_id, data in d4_m1.items()
        if isinstance(data, Mapping)
    ]

    # D4.M2 - Degree
    degree = _get(measures, "size_complexity", "d4_m2_degree")
    d4_m2 = _get(measures_per_model, "size_complexity", "d4_m2_degree", default={})
    if not isinstance(d4_m2, Mapping):
        d4_m2 = {}
    avg_degree_histogram = create_histogram_data([v.get("avg_degree") for v in d4_m2.values() if isinstance(v, Mapping)])
    avg_in_degree_histogram = create_histogram_data([v.get("avg_in_degree") for v in d4_m2.values() if isinstance(v, Mapping)])
    avg_out_degree_histogram = create_histogram_data([v.get("avg_out_degree") for v in d4_m2.values() if isinstance(v, Mapping)])
    degree_median_histogram = create_histogram_data([v.get("degree_median") for v in d4_m2.values() if isinstance(v, Mapping)])
    degree_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "avgDegree": float(data.get("avg_degree", 0) or 0),
                    "avgInDegree": float(data.get("avg_in_degree", 0) or 0),
                    "avgOutDegree": float(data.get("avg_out_degree", 0) or 0),
                    "degreeMedian": float(data.get("degree_median", 0) or 0),
                }
                for model_id, data in d4_m2.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["avgDegree"],
            reverse=True,
        )[:10]
        if d4_m2
        else []
    )

    # D4.M3 - Connectivity
    connectivity = _get(measures, "size_complexity", "d4_m3_connectivity")
    d4_m3 = _get(measures_per_model, "size_complexity", "d4_m3_connectivity", default={})
    if not isinstance(d4_m3, Mapping):
        d4_m3 = {}
    n_components_histogram = create_histogram_data([v.get("n_components") for v in d4_m3.values() if isinstance(v, Mapping)])
    largest_component_histogram = create_histogram_data([v.get("largest_component_size") for v in d4_m3.values() if isinstance(v, Mapping)])
    isolated_node_count_histogram = create_histogram_data([v.get("isolated_node_count") for v in d4_m3.values() if isinstance(v, Mapping)])
    isolated_node_share_histogram = create_share_histogram_data([v.get("isolated_node_share") for v in d4_m3.values() if isinstance(v, Mapping)])
    connectivity_top10_isolated = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "isolatedNodeShare": float(data.get("isolated_node_share", 0) or 0),
                    "isolatedNodeCount": int(data.get("isolated_node_count", 0) or 0),
                    "nComponents": int(data.get("n_components", 0) or 0),
                    "largestComponentSize": int(data.get("largest_component_size", 0) or 0),
                }
                for model_id, data in d4_m3.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["isolatedNodeShare"],
            reverse=True,
        )[:10]
        if d4_m3
        else []
    )

    # D4.M4 - Containment Depth
    containment_depth = _get(measures, "size_complexity", "d4_m4_containment_depth")
    d4_m4 = _get(measures_per_model, "size_complexity", "d4_m4_containment_depth", default={})
    if not isinstance(d4_m4, Mapping):
        d4_m4 = {}
    max_depth_histogram = create_histogram_data([v.get("max_depth") for v in d4_m4.values() if isinstance(v, Mapping)])
    mean_depth_histogram = create_histogram_data([v.get("mean_depth") for v in d4_m4.values() if isinstance(v, Mapping)])
    contained_node_share_histogram = create_share_histogram_data([v.get("contained_node_share") for v in d4_m4.values() if isinstance(v, Mapping)])
    depth_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "maxDepth": int(data.get("max_depth", 0) or 0),
                    "meanDepth": float(data.get("mean_depth", 0) or 0),
                    "rootCount": int(data.get("root_count", 0) or 0),
                    "containedNodeShare": float(data.get("contained_node_share", 0) or 0),
                }
                for model_id, data in d4_m4.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["maxDepth"],
            reverse=True,
        )[:10]
        if d4_m4
        else []
    )

    return {
        "modelSize": model_size,
        "modelSizeNodeHistogram": model_size_node_histogram,
        "modelSizeEdgeHistogram": model_size_edge_histogram,
        "modelSizeElementHistogram": model_size_element_histogram,
        "modelSizeEdgeNodeRatioHistogram": model_size_ratio_histogram,
        "modelSizeScatterData": model_size_scatter_data,
        "modelSizeTop10": model_size_top10,
        "degree": degree,
        "avgDegreeHistogram": avg_degree_histogram,
        "avgInDegreeHistogram": avg_in_degree_histogram,
        "avgOutDegreeHistogram": avg_out_degree_histogram,
        "degreeMedianHistogram": degree_median_histogram,
        "degreeTop10": degree_top10,
        "connectivity": connectivity,
        "nComponentsHistogram": n_components_histogram,
        "largestComponentSizeHistogram": largest_component_histogram,
        "isolatedNodeCountHistogram": isolated_node_count_histogram,
        "isolatedNodeShareHistogram": isolated_node_share_histogram,
        "connectivityTop10": connectivity_top10_isolated,
        "containmentDepth": containment_depth,
        "maxDepthHistogram": max_depth_histogram,
        "meanDepthHistogram": mean_depth_histogram,
        "containedNodeShareHistogram": contained_node_share_histogram,
        "depthTop10": depth_top10,
    }

