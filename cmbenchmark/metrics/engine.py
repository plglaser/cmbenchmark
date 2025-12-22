"""Metrics computation engine."""

from typing import Dict, Any, List
from pathlib import Path
import json
from cmbenchmark.types.ir import IR
from cmbenchmark.metrics.cross_language import compute_cross_language_metrics
from cmbenchmark.metrics.language_specific import compute_language_specific_metrics


def compute_metrics(ir_path: str) -> Dict[str, Any]:
    """
    Compute metrics for all IR models in the given directory.

    Args:
        ir_path: Path to directory containing IR JSON files

    Returns:
        Dictionary containing computed metrics
    """
    ir_dir = Path(ir_path)
    ir_files = list(ir_dir.glob("*.json"))

    if not ir_files:
        return {"error": "No IR files found in directory"}

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
        return {"error": "No valid IR models could be loaded"}

    # Compute cross-language metrics
    cross_metrics = compute_cross_language_metrics(ir_models)

    # Compute language-specific metrics
    lang_metrics = compute_language_specific_metrics(ir_models)

    # Combine metrics
    metrics = {
        "num_models": len(ir_models),
        **cross_metrics,
        "language_specific": lang_metrics.get("metrics", {}),
    }

    return metrics


def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save metrics to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

