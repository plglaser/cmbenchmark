"""Computation functions for construct coverage measures (D3)."""

from typing import List, Dict, Tuple
from collections import Counter, defaultdict

from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.constructs import ConstructDef
from cmbenchmark.types.profile import ConstructCoverageProfile
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
    
    # Track which constructs we've seen (for presence)
    seen_constructs: Dict[str, bool] = {}
    
    # Match nodes
    for node in ir.nodes:
        matched = False
        for construct_id, construct_def in constructs.items():
            # Skip UNKNOWN constructs from matching
            if construct_id.startswith("UNKNOWN"):
                continue
            
            if construct_def.matches_node(node.type, node.data):
                construct_counts[construct_id] += 1
                seen_constructs[construct_id] = True
                matched = True
                break
        
        if not matched:
            unknown_node_types[node.type] += 1
    
    # Match edges
    for edge in ir.edges:
        matched = False
        for construct_id, construct_def in constructs.items():
            # Skip UNKNOWN constructs from matching
            if construct_id.startswith("UNKNOWN"):
                continue
            
            if construct_def.matches_edge(edge.type, edge.data):
                construct_counts[construct_id] += 1
                seen_constructs[construct_id] = True
                matched = True
                break
        
        if not matched:
            unknown_edge_types[edge.type] += 1
    
    return dict(construct_counts), dict(unknown_node_types), dict(unknown_edge_types)


def compute_construct_measures(
    ir_models: List[IR],
    construct_profile: ConstructCoverageProfile,
) -> Tuple[ConstructMeasuresDataset, ConstructMeasuresPerModel]:
    """
    Compute construct coverage measures (D3.M1, D3.M3) for IR models.
    
    Args:
        ir_models: List of IR models to analyze
        construct_profile: Configuration for construct measures
        
    Returns:
        Tuple of (dataset_measures, per_model_measures)
    """
    if not construct_profile.enabled or not construct_profile.constructs:
        # Return empty measures if not enabled
        empty_dataset = ConstructMeasuresDataset(
            d3_m1_construct_presence=D3M1ConstructPresenceDataset(
                constructs_available_count=0,
                constructs_observed_count=0,
                coverage_share=0.0,
                coverage_share_stats=_compute_distribution_summary([]),
            ),
            d3_m3_construct_frequency=D3M3ConstructFrequencyDataset(),
        )
        empty_per_model = ConstructMeasuresPerModel()
        return empty_dataset, empty_per_model
    
    constructs = construct_profile.constructs
    
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
    for ir in ir_models:
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
        per_model_d3m3[ir.id] = D3M3ConstructFrequencyPerModel(
            count_by_construct=dict(construct_counts),
        )
        
        # Aggregate for dataset-level
        for construct_id, count in construct_counts.items():
            dataset_construct_counts[construct_id] += count
        
        total_unknown_nodes += unknown_node_count
        total_unknown_edges += unknown_edge_count
        total_elements += total_model_elements
        
        for unknown_type, count in all_unknown_types.items():
            unknown_type_examples_dataset[unknown_type] += count
    
    # D3.M1: Dataset-level
    constructs_observed_dataset = len([
        cid for cid in available_constructs.keys()
        if dataset_construct_counts.get(cid, 0) > 0
    ])
    coverage_share_dataset = constructs_observed_dataset / max(1, constructs_available_count)
    unknown_type_share_dataset = (total_unknown_nodes + total_unknown_edges) / max(1, total_elements)
    
    dataset_d3m1 = D3M1ConstructPresenceDataset(
        constructs_available_count=constructs_available_count,
        constructs_observed_count=constructs_observed_dataset,
        coverage_share=coverage_share_dataset,
        coverage_share_stats=_compute_distribution_summary(coverage_shares),
        unknown_type_share_dataset=unknown_type_share_dataset,
    )
    
    # D3.M3: Dataset-level
    dataset_d3m3 = D3M3ConstructFrequencyDataset(
        dataset_count_by_construct=dict(dataset_construct_counts),
    )
    
    # Combine into dataset result
    dataset_result = ConstructMeasuresDataset(
        d3_m1_construct_presence=dataset_d3m1,
        d3_m3_construct_frequency=dataset_d3m3,
    )
    
    # Combine into per-model result
    per_model_result = ConstructMeasuresPerModel(
        d3_m1_construct_presence=per_model_d3m1,
        d3_m3_construct_frequency=per_model_d3m3,
    )
    
    return dataset_result, per_model_result
