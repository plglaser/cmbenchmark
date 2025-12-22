"""Diversity metrics for model datasets."""

from typing import List
from cmbenchmark.types.ir import IR


def compute_diversity_metrics(ir_models: List[IR]) -> dict:
    """
    Compute diversity metrics across all models.

    Args:
        ir_models: List of IR models

    Returns:
        Dictionary with diversity metrics
    """
    # Language-related metrics removed - focusing on single language at a time
    return {}

