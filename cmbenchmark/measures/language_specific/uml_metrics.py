"""UML-specific metrics."""

from typing import List
from cmbenchmark.types.ir import IR
from .constructs import compute_construct_metrics


def compute_uml_metrics(ir_models: List[IR]) -> dict:
    """
    Compute UML-specific metrics.

    Args:
        ir_models: List of IR models with language="UML"

    Returns:
        Dictionary with UML-specific metrics organized by category
    """
    if not ir_models:
        return {}

    # Compute construct-related metrics
    construct_metrics = compute_construct_metrics(ir_models)

    return {
        "num_uml_models": len(ir_models),
        "constructs": construct_metrics,
    }

