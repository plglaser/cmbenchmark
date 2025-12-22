"""Metrics service for computing metrics on IR models."""

from pathlib import Path
from typing import Dict, Any, List
import json
from cmbenchmark.types.models import MetricsResult
from cmbenchmark.types.ir import IR
from cmbenchmark.metrics.cross_language import compute_cross_language_metrics
from cmbenchmark.metrics.language_specific import compute_language_specific_metrics


def compute_metrics(ir_path: str) -> MetricsResult:
    """
    Compute metrics for all IR models in the given directory.

    Args:
        ir_path: Path to directory containing IR JSON files

    Returns:
        MetricsResult object containing computed metrics
    """
    ir_dir = Path(ir_path)
    ir_files = list(ir_dir.glob("*.json"))

    if not ir_files:
        raise ValueError("No IR files found in directory")

    # Load all IR models
    ir_models: List[IR] = []
    for ir_file in ir_files:
        try:
            ir = IR.load(str(ir_file))
            ir_models.append(ir)
        except Exception as e:
            # Skip files that can't be loaded
            continue

    if not ir_models:
        raise ValueError("No valid IR models could be loaded")

    # Compute cross-language metrics
    cross_metrics = compute_cross_language_metrics(ir_models)

    # Compute language-specific metrics
    lang_metrics = compute_language_specific_metrics(ir_models)

    # Combine metrics into MetricsResult
    return MetricsResult(
        num_models=len(ir_models),
        avg_elements_per_model=cross_metrics.get("avg_elements_per_model", 0.0),
        avg_nodes_per_model=cross_metrics.get("avg_nodes_per_model", 0.0),
        avg_edges_per_model=cross_metrics.get("avg_edges_per_model", 0.0),
        total_elements=cross_metrics.get("total_elements", 0),
        total_nodes=cross_metrics.get("total_nodes", 0),
        total_edges=cross_metrics.get("total_edges", 0),
        edge_to_node_ratio=cross_metrics.get("edge_to_node_ratio", 0.0),
        language_specific=lang_metrics.get("metrics", {}),
    )


def save_metrics(metrics: MetricsResult, output_path: str) -> None:
    """
    Save metrics to JSON file.

    Args:
        metrics: MetricsResult object to save
        output_path: Path to output JSON file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2)

