"""Size and shape metrics for models."""

from typing import List
from cmbenchmark.types.ir import IR


def compute_size_shape_metrics(ir_models: List[IR]) -> dict:
    """
    Compute size and shape metrics across all models.

    Args:
        ir_models: List of IR models

    Returns:
        Dictionary with size and shape metrics
    """
    if not ir_models:
        return {}

    total_elements = sum(len(ir.nodes) + len(ir.edges) for ir in ir_models)
    num_models = len(ir_models)
    avg_elements_per_model = total_elements / num_models if num_models > 0 else 0

    total_nodes = sum(len(ir.nodes) for ir in ir_models)
    total_edges = sum(len(ir.edges) for ir in ir_models)
    avg_nodes_per_model = total_nodes / num_models if num_models > 0 else 0
    avg_edges_per_model = total_edges / num_models if num_models > 0 else 0

    # Edge-to-node ratio
    edge_to_node_ratio = total_edges / total_nodes if total_nodes > 0 else 0

    return {
        "avg_elements_per_model": round(avg_elements_per_model, 2),
        "avg_nodes_per_model": round(avg_nodes_per_model, 2),
        "avg_edges_per_model": round(avg_edges_per_model, 2),
        "total_elements": total_elements,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "edge_to_node_ratio": round(edge_to_node_ratio, 2),
    }

