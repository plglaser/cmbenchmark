"""Computation functions for size & complexity measures (D4)."""

from __future__ import annotations

import statistics
from collections import deque
from typing import Dict, List, Tuple, Optional, Callable, Iterable

from cmbenchmark.types.ir import IR, Edge
from cmbenchmark.types.measures import (
    D4M1ModelSizeDataset,
    D4M1ModelSizePerModel,
    D4M2DegreeDataset,
    D4M2DegreePerModel,
    D4M3ConnectivityDataset,
    D4M3ConnectivityPerModel,
    D4M4ContainmentDepthDataset,
    D4M4ContainmentDepthPerModel,
    SizeComplexityMeasuresDataset,
    SizeComplexityMeasuresPerModel,
)
from cmbenchmark.measures.parsing_measures import _compute_distribution_summary


def _safe_mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_median(values: List[float]) -> float:
    return statistics.median(values) if values else 0.0


def _is_containment_edge(edge: Edge, language: str) -> bool:
    edge_type = (edge.type or "").strip().lower()
    lang = (language or "").strip().lower()

    # Language-specific containment semantics
    if "archimate" in lang:
        if edge_type in {"composition", "aggregation"}:
            return True
        return False

    if "ecore" in lang:
        if edge_type in {"contains", "containment"}:
            return True
        data = edge.data or {}
        return bool(data.get("containment") is True)

    # Fallback: best-effort across languages
    if edge_type in {"contains", "containment", "composition", "aggregation"}:
        return True
    data = edge.data or {}
    return bool(data.get("containment") is True)


def _compute_degree_stats(ir: IR) -> Tuple[float, float, float, List[int], List[int], List[int], float]:
    node_ids = [node.id for node in ir.nodes]
    in_degree: Dict[str, int] = {node_id: 0 for node_id in node_ids}
    out_degree: Dict[str, int] = {node_id: 0 for node_id in node_ids}

    for edge in ir.edges:
        if edge.sourceId in out_degree:
            out_degree[edge.sourceId] += 1
        if edge.targetId in in_degree:
            in_degree[edge.targetId] += 1

    in_values = list(in_degree.values())
    out_values = list(out_degree.values())
    total_values = [in_values[i] + out_values[i] for i in range(len(node_ids))]

    avg_degree = _safe_mean([float(v) for v in total_values])
    avg_in = _safe_mean([float(v) for v in in_values])
    avg_out = _safe_mean([float(v) for v in out_values])
    degree_median = float(_safe_median([float(v) for v in total_values]))

    return avg_degree, avg_in, avg_out, total_values, in_values, out_values, degree_median


def _compute_connectivity(ir: IR) -> Tuple[int, int, int, float, List[int]]:
    node_ids = [node.id for node in ir.nodes]
    adjacency: Dict[str, set] = {node_id: set() for node_id in node_ids}

    for edge in ir.edges:
        if edge.sourceId not in adjacency or edge.targetId not in adjacency:
            continue
        adjacency[edge.sourceId].add(edge.targetId)
        adjacency[edge.targetId].add(edge.sourceId)

    visited = set()
    component_sizes: List[int] = []

    for node_id in node_ids:
        if node_id in visited:
            continue
        queue = deque([node_id])
        visited.add(node_id)
        size = 0
        while queue:
            cur = queue.popleft()
            size += 1
            for nxt in adjacency[cur]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        component_sizes.append(size)

    n_components = len(component_sizes)
    largest_component_size = max(component_sizes) if component_sizes else 0
    isolated_node_count = sum(1 for node_id, neighbors in adjacency.items() if len(neighbors) == 0)
    node_count = len(node_ids)
    isolated_node_share = isolated_node_count / max(1, node_count)

    return n_components, largest_component_size, isolated_node_count, isolated_node_share, component_sizes


def _compute_containment_depth(ir: IR) -> Tuple[int, float, float, List[int], int, float, int]:
    node_ids = [node.id for node in ir.nodes]
    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
    in_degree: Dict[str, int] = {node_id: 0 for node_id in node_ids}

    for edge in ir.edges:
        if not _is_containment_edge(edge, ir.language):
            continue
        if edge.sourceId not in adjacency or edge.targetId not in adjacency:
            continue
        adjacency[edge.sourceId].append(edge.targetId)
        in_degree[edge.targetId] += 1

    roots = [node_id for node_id in node_ids if in_degree[node_id] == 0]
    if not roots and node_ids:
        roots = list(node_ids)

    depth: Dict[str, int] = {node_id: 0 for node_id in node_ids}
    queue = deque(roots)
    in_queue = set(roots)
    max_allowed_depth = max(1, len(node_ids))

    while queue:
        parent = queue.popleft()
        in_queue.discard(parent)
        parent_depth = depth[parent]
        for child in adjacency[parent]:
            next_depth = parent_depth + 1
            if next_depth > max_allowed_depth:
                continue
            if next_depth > depth[child]:
                depth[child] = next_depth
                if child not in in_queue:
                    queue.append(child)
                    in_queue.add(child)

    depth_values = [depth[node_id] for node_id in node_ids]
    max_depth = max(depth_values) if depth_values else 0
    mean_depth = _safe_mean([float(v) for v in depth_values])
    median_depth = float(_safe_median([float(v) for v in depth_values]))
    contained_node_count = sum(1 for v in depth_values if v > 0)
    contained_node_share = contained_node_count / max(1, len(node_ids))
    root_count = len(roots) if node_ids else 0

    return (
        max_depth,
        mean_depth,
        median_depth,
        depth_values,
        root_count,
        contained_node_share,
        contained_node_count,
    )


def compute_size_complexity_measures(
    ir_models: Iterable[IR],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
    total_models: Optional[int] = None,
) -> Tuple[SizeComplexityMeasuresDataset, SizeComplexityMeasuresPerModel]:
    """Compute size & complexity measures (D4.M1-D4.M4) for IR models."""
    per_model_m1: Dict[str, D4M1ModelSizePerModel] = {}
    per_model_m2: Dict[str, D4M2DegreePerModel] = {}
    per_model_m3: Dict[str, D4M3ConnectivityPerModel] = {}
    per_model_m4: Dict[str, D4M4ContainmentDepthPerModel] = {}

    node_counts: List[float] = []
    edge_counts: List[float] = []
    element_counts: List[float] = []
    edge_node_ratios: List[float] = []

    avg_degree_values: List[float] = []
    avg_in_degree_values: List[float] = []
    avg_out_degree_values: List[float] = []
    degree_medians: List[float] = []

    n_components_values: List[float] = []
    largest_component_sizes: List[float] = []
    isolated_node_counts: List[float] = []
    isolated_node_shares: List[float] = []

    max_depth_values: List[float] = []
    mean_depth_values: List[float] = []
    contained_node_shares: List[float] = []

    total_node_count = 0
    total_edge_count = 0
    total_element_count = 0
    total_components = 0
    total_isolated_nodes = 0
    total_contained_nodes = 0
    total_root = 0

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

        node_count = len(ir.nodes)
        edge_count = len(ir.edges)
        element_count = node_count + edge_count
        edge_node_ratio = edge_count / max(1, node_count)

        per_model_m1[ir.id] = D4M1ModelSizePerModel(
            node_count=node_count,
            edge_count=edge_count,
            element_count=element_count,
            edge_node_ratio=edge_node_ratio,
        )

        total_node_count += node_count
        total_edge_count += edge_count
        total_element_count += element_count

        node_counts.append(float(node_count))
        edge_counts.append(float(edge_count))
        element_counts.append(float(element_count))
        edge_node_ratios.append(float(edge_node_ratio))

        (
            avg_degree,
            avg_in_degree,
            avg_out_degree,
            degree_values,
            in_degree_values,
            out_degree_values,
            degree_median,
        ) = _compute_degree_stats(ir)

        per_model_m2[ir.id] = D4M2DegreePerModel(
            avg_degree=avg_degree,
            avg_in_degree=avg_in_degree,
            avg_out_degree=avg_out_degree,
            degree_stats=_compute_distribution_summary([float(v) for v in degree_values]),
            in_degree_stats=_compute_distribution_summary([float(v) for v in in_degree_values]),
            out_degree_stats=_compute_distribution_summary([float(v) for v in out_degree_values]),
            degree_median=degree_median,
        )

        avg_degree_values.append(avg_degree)
        avg_in_degree_values.append(avg_in_degree)
        avg_out_degree_values.append(avg_out_degree)
        degree_medians.append(degree_median)

        (
            n_components,
            largest_component_size,
            isolated_node_count,
            isolated_node_share,
            component_sizes,
        ) = _compute_connectivity(ir)

        per_model_m3[ir.id] = D4M3ConnectivityPerModel(
            n_components=n_components,
            largest_component_size=largest_component_size,
            isolated_node_count=isolated_node_count,
            isolated_node_share=isolated_node_share,
            component_size_stats=_compute_distribution_summary([float(v) for v in component_sizes]),
        )

        n_components_values.append(float(n_components))
        largest_component_sizes.append(float(largest_component_size))
        isolated_node_counts.append(float(isolated_node_count))
        isolated_node_shares.append(float(isolated_node_share))
        total_components += n_components
        total_isolated_nodes += isolated_node_count

        (
            max_depth,
            mean_depth,
            median_depth,
            depth_values,
            root_count,
            contained_node_share,
            contained_node_count,
        ) = _compute_containment_depth(ir)

        per_model_m4[ir.id] = D4M4ContainmentDepthPerModel(
            max_depth=max_depth,
            mean_depth=mean_depth,
            median_depth=median_depth,
            depth_stats=_compute_distribution_summary([float(v) for v in depth_values]),
            root_count=root_count,
            contained_node_share=contained_node_share,
        )

        max_depth_values.append(float(max_depth))
        mean_depth_values.append(float(mean_depth))
        contained_node_shares.append(float(contained_node_share))
        total_contained_nodes += contained_node_count
        total_root += root_count

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

    dataset_m1 = D4M1ModelSizeDataset(
        total_node_count=total_node_count,
        total_edge_count=total_edge_count,
        total_element_count=total_element_count,
        node_count_stats=_compute_distribution_summary(node_counts),
        edge_count_stats=_compute_distribution_summary(edge_counts),
        element_count_stats=_compute_distribution_summary(element_counts),
        edge_node_ratio_stats=_compute_distribution_summary(edge_node_ratios),
    )

    dataset_m2 = D4M2DegreeDataset(
        avg_degree_stats=_compute_distribution_summary(avg_degree_values),
        avg_in_degree_stats=_compute_distribution_summary(avg_in_degree_values),
        avg_out_degree_stats=_compute_distribution_summary(avg_out_degree_values),
        degree_median_stats=_compute_distribution_summary(degree_medians),
    )

    dataset_m3 = D4M3ConnectivityDataset(
        n_components_stats=_compute_distribution_summary(n_components_values),
        largest_component_size_stats=_compute_distribution_summary(largest_component_sizes),
        isolated_node_count_stats=_compute_distribution_summary(isolated_node_counts),
        isolated_node_share_stats=_compute_distribution_summary(isolated_node_shares),
        total_components=total_components,
        total_isolated_nodes=total_isolated_nodes,
    )

    dataset_m4 = D4M4ContainmentDepthDataset(
        max_depth_stats=_compute_distribution_summary(max_depth_values),
        mean_depth_stats=_compute_distribution_summary(mean_depth_values),
        contained_node_share_stats=_compute_distribution_summary(contained_node_shares),
        total_contained_nodes=total_contained_nodes,
        total_root=total_root,
    )

    dataset = SizeComplexityMeasuresDataset(
        d4_m1_model_size=dataset_m1,
        d4_m2_degree=dataset_m2,
        d4_m3_connectivity=dataset_m3,
        d4_m4_containment_depth=dataset_m4,
    )

    per_model = SizeComplexityMeasuresPerModel(
        d4_m1_model_size=per_model_m1,
        d4_m2_degree=per_model_m2,
        d4_m3_connectivity=per_model_m3,
        d4_m4_containment_depth=per_model_m4,
    )

    return dataset, per_model
