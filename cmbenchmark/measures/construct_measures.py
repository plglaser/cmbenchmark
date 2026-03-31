"""Computation functions for construct coverage measures (D3)."""

from typing import List, Dict, Tuple, Any, Optional, Callable, Iterable
from collections import Counter, defaultdict
import math

from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.constructs import ConstructDef
from cmbenchmark.types.measures import (
    ConstructMeasuresDataset,
    ConstructMeasuresPerModel,
    D3M1ConstructPresenceDataset,
    D3M1ConstructPresencePerModel,
    D3M3ConstructFrequencyDataset,
    D3M3ConstructFrequencyPerModel,
    DistributionSummary,
)
from cmbenchmark.measures.parsing_measures import _compute_distribution_summary


def _construct_group(construct_def: ConstructDef) -> str:
    """
    Determine the high-level grouping label for a construct.

    For ArchiMate we typically use `meta.layer`; for Ecore `meta.group`.
    Falls back to "—" if no grouping is present.
    """
    meta = construct_def.meta or {}
    return (
        meta.get("layer")
        or meta.get("group")
        or meta.get("category")
        or meta.get("kind")
        or "—"
    )


def _match_constructs_for_ir(
    ir: IR,
    constructs: Dict[str, ConstructDef],
) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    """
    Match constructs against an IR model.
    
    Returns:
        Tuple of (construct_counts, unknown_node_types, unknown_edge_types)
        - construct_counts: construct_id -> count
        - unknown_node_types: raw_type -> count
        - unknown_edge_types: raw_type -> count
    """
    construct_counts: Dict[str, int] = defaultdict(int)
    unknown_node_types: Dict[str, int] = defaultdict(int)
    unknown_edge_types: Dict[str, int] = defaultdict(int)
    
    # Match nodes
    for node in ir.nodes:
        matched_any = False
        for construct_id, construct_def in constructs.items():
            # Skip UNKNOWN constructs from matching
            if construct_id.startswith("UNKNOWN"):
                continue

            if construct_def.matches_node(node.type, node.data):
                construct_counts[construct_id] += 1
                matched_any = True

        if not matched_any:
            unknown_node_types[node.type] += 1
    
    # Match edges
    for edge in ir.edges:
        matched_any = False
        for construct_id, construct_def in constructs.items():
            # Skip UNKNOWN constructs from matching
            if construct_id.startswith("UNKNOWN"):
                continue
            
            if construct_def.matches_edge(edge.type, edge.data):
                construct_counts[construct_id] += 1
                matched_any = True

        if not matched_any:
            unknown_edge_types[edge.type] += 1
    
    return dict(construct_counts), dict(unknown_node_types), dict(unknown_edge_types)


def _compute_utilization_entropy(relative_frequency_by_construct: Dict[str, float]) -> float:
    """Compute normalized utilization entropy in [0, 1] from relative frequencies."""
    probs = [float(p) for p in relative_frequency_by_construct.values() if p > 0]
    k = len(probs)
    if k <= 1:
        return 0.0
    entropy = -sum(p * math.log(p) for p in probs)
    return entropy / math.log(k)


def compute_construct_measures(
    ir_models: Iterable[IR],
    constructs: Dict[str, ConstructDef],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
    total_models: Optional[int] = None,
) -> Tuple[ConstructMeasuresDataset, ConstructMeasuresPerModel]:
    """
    Compute construct coverage measures (D3.M1, D3.M3) for IR models.
    
    Args:
        ir_models: List of IR models to analyze
        constructs: Construct definitions for matching
        
    Returns:
        Tuple of (dataset_measures, per_model_measures)
    """
    if not constructs:
        # Return empty measures if not enabled
        empty_dataset = ConstructMeasuresDataset(
            d3_m1_construct_presence=D3M1ConstructPresenceDataset(
                constructs_available_count=0,
                constructs_observed_count=0,
                coverage_share=0.0,
                coverage_share_stats=_compute_distribution_summary([]),
                score=0.0,
            ),
            d3_m3_construct_frequency=D3M3ConstructFrequencyDataset(score=0.0),
            score=0.0,
        )
        empty_per_model = ConstructMeasuresPerModel()
        return empty_dataset, empty_per_model
    
    # Filter out UNKNOWN constructs from available count
    available_constructs = {
        cid: cdef for cid, cdef in constructs.items()
        if not cid.startswith("UNKNOWN")
    }
    constructs_available_count = len(available_constructs)
    
    # Per-model accumulators
    per_model_d3m1: Dict[str, D3M1ConstructPresencePerModel] = {}
    per_model_d3m3: Dict[str, D3M3ConstructFrequencyPerModel] = {}
    
    # Dataset-level accumulators
    dataset_construct_counts: Dict[str, int] = defaultdict(int)
    coverage_shares: List[float] = []
    total_unknown_nodes = 0
    total_unknown_edges = 0
    total_elements = 0
    unknown_type_examples_dataset: Dict[str, int] = defaultdict(int)
    
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

        # Match constructs
        construct_counts, unknown_node_types, unknown_edge_types = _match_constructs_for_ir(
            ir, constructs
        )
        
        # D3.M1: Construct Presence (per-model)
        constructs_observed_count = len([cid for cid in construct_counts.keys() if construct_counts[cid] > 0])
        coverage_share = constructs_observed_count / max(1, constructs_available_count)
        coverage_shares.append(coverage_share)
        
        # Track which constructs are present
        present_constructs = {
            cid: construct_counts.get(cid, 0) > 0
            for cid in available_constructs.keys()
        }
        
        # Unknown type diagnostics
        unknown_node_count = sum(unknown_node_types.values())
        unknown_edge_count = sum(unknown_edge_types.values())
        total_model_elements = len(ir.nodes) + len(ir.edges)
        unknown_type_share = (unknown_node_count + unknown_edge_count) / max(1, total_model_elements)
        
        # Top-K unknown types (top 10)
        all_unknown_types = {**unknown_node_types, **unknown_edge_types}
        top_unknown = dict(sorted(all_unknown_types.items(), key=lambda x: x[1], reverse=True)[:10])
        
        per_model_d3m1[ir.id] = D3M1ConstructPresencePerModel(
            constructs_available_count=constructs_available_count,
            constructs_observed_count=constructs_observed_count,
            coverage_share=coverage_share,
            present_constructs=present_constructs,
            unknown_node_type_count=unknown_node_count,
            unknown_edge_type_count=unknown_edge_count,
            unknown_type_share=unknown_type_share,
            unknown_type_examples=top_unknown,
        )
        
        # D3.M3: Construct Frequency (per-model)
        total_construct_instances = sum(construct_counts.values())
        relative_frequency_by_construct = {
            cid: (construct_counts.get(cid, 0) / total_construct_instances)
            if total_construct_instances > 0
            else 0.0
            for cid in available_constructs.keys()
        }
        utilization_entropy = _compute_utilization_entropy(relative_frequency_by_construct)

        per_model_d3m3[ir.id] = D3M3ConstructFrequencyPerModel(
            count_by_construct=dict(construct_counts),
            total_construct_instances=total_construct_instances,
            relative_frequency_by_construct=relative_frequency_by_construct,
            utilization_entropy=utilization_entropy,
        )
        
        # Aggregate for dataset-level
        for construct_id, count in construct_counts.items():
            dataset_construct_counts[construct_id] += count
        
        total_unknown_nodes += unknown_node_count
        total_unknown_edges += unknown_edge_count
        total_elements += total_model_elements
        
        for unknown_type, count in all_unknown_types.items():
            unknown_type_examples_dataset[unknown_type] += count

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
    
    # D3.M1: Dataset-level
    constructs_observed_dataset = len([
        cid for cid in available_constructs.keys()
        if dataset_construct_counts.get(cid, 0) > 0
    ])
    coverage_share_dataset = constructs_observed_dataset / max(1, constructs_available_count)
    unknown_type_share_dataset = (total_unknown_nodes + total_unknown_edges) / max(1, total_elements)

    # Construct catalog (metadata for UI/reporting)
    construct_catalog: Dict[str, Dict[str, Any]] = {}
    for cid, cdef in available_constructs.items():
        construct_catalog[cid] = {
            "id": cid,
            "description": cdef.description,
            "kind": cdef.kind,
            "match_type": cdef.match_type,
            "group": _construct_group(cdef),
            "meta": cdef.meta or {},
        }

    # Missing constructs at dataset level (never observed)
    missing_constructs: List[Dict[str, Any]] = []
    for cid, cdef in available_constructs.items():
        if dataset_construct_counts.get(cid, 0) <= 0:
            missing_constructs.append(
                {
                    "constructId": cid,
                    "group": _construct_group(cdef),
                    "description": cdef.description,
                    "kind": cdef.kind,
                }
            )
    missing_constructs.sort(key=lambda x: (str(x.get("group") or ""), str(x.get("constructId") or "")))

    # Coverage breakdowns by group and kind
    coverage_by_group: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"available": 0, "observed": 0, "missing": 0, "coverage_share": 0.0})
    coverage_by_kind: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"available": 0, "observed": 0, "missing": 0, "coverage_share": 0.0})

    for cid, cdef in available_constructs.items():
        group = _construct_group(cdef)
        kind = cdef.kind
        coverage_by_group[group]["available"] += 1
        coverage_by_kind[kind]["available"] += 1
        if dataset_construct_counts.get(cid, 0) > 0:
            coverage_by_group[group]["observed"] += 1
            coverage_by_kind[kind]["observed"] += 1

    for group, stats in coverage_by_group.items():
        stats["missing"] = stats["available"] - stats["observed"]
        stats["coverage_share"] = stats["observed"] / max(1, stats["available"])
    for kind, stats in coverage_by_kind.items():
        stats["missing"] = stats["available"] - stats["observed"]
        stats["coverage_share"] = stats["observed"] / max(1, stats["available"])

    # Keep only top unknown types to avoid bloating JSON
    unknown_type_examples_dataset_top = dict(
        sorted(unknown_type_examples_dataset.items(), key=lambda x: x[1], reverse=True)[:25]
    )
    
    score = 100.0 * coverage_share_dataset * (1.0 - unknown_type_share_dataset)
    score = max(0.0, min(100.0, score))

    dataset_d3m1 = D3M1ConstructPresenceDataset(
        constructs_available_count=constructs_available_count,
        constructs_observed_count=constructs_observed_dataset,
        coverage_share=coverage_share_dataset,
        coverage_share_stats=_compute_distribution_summary(coverage_shares),
        unknown_type_share_dataset=unknown_type_share_dataset,
        score=score,
        construct_catalog=construct_catalog,
        missing_constructs=missing_constructs,
        coverage_by_group=dict(coverage_by_group),
        coverage_by_kind=dict(coverage_by_kind),
        unknown_node_type_count_dataset=total_unknown_nodes,
        unknown_edge_type_count_dataset=total_unknown_edges,
        unknown_type_examples_dataset=unknown_type_examples_dataset_top,
    )
    
    # D3.M3: Dataset-level
    dataset_total_construct_instances = sum(dataset_construct_counts.values())
    dataset_relative_frequency_by_construct = {
        cid: (dataset_construct_counts.get(cid, 0) / dataset_total_construct_instances)
        if dataset_total_construct_instances > 0
        else 0.0
        for cid in available_constructs.keys()
    }
    dataset_utilization_entropy = _compute_utilization_entropy(dataset_relative_frequency_by_construct)
    d3m3_score = max(0.0, min(100.0, 100.0 * dataset_utilization_entropy))

    dataset_d3m3 = D3M3ConstructFrequencyDataset(
        dataset_count_by_construct=dict(dataset_construct_counts),
        dataset_total_construct_instances=dataset_total_construct_instances,
        dataset_relative_frequency_by_construct=dataset_relative_frequency_by_construct,
        dataset_utilization_entropy=dataset_utilization_entropy,
        score=d3m3_score,
    )
    
    # Combine into dataset result
    construct_dimension_score = (dataset_d3m1.score + dataset_d3m3.score) / 2.0
    construct_dimension_score = max(0.0, min(100.0, construct_dimension_score))

    dataset_result = ConstructMeasuresDataset(
        d3_m1_construct_presence=dataset_d3m1,
        d3_m3_construct_frequency=dataset_d3m3,
        score=construct_dimension_score,
    )
    
    # Combine into per-model result
    per_model_result = ConstructMeasuresPerModel(
        d3_m1_construct_presence=per_model_d3m1,
        d3_m3_construct_frequency=per_model_d3m3,
    )
    
    return dataset_result, per_model_result
