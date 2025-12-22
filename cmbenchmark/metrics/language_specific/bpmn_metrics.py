"""BPMN-specific metrics."""

from typing import List
from cmbenchmark.types.ir import IR


def compute_bpmn_metrics(ir_models: List[IR]) -> dict:
    """
    Compute BPMN-specific metrics.

    Args:
        ir_models: List of IR models with language="BPMN"

    Returns:
        Dictionary with BPMN-specific metrics
    """
    if not ir_models:
        return {}

    # Placeholder for BPMN-specific metrics
    # In a full implementation, this would analyze BPMN-specific elements
    # such as tasks, events, gateways, flows, pools, lanes, etc.

    return {
        "num_bpmn_models": len(ir_models),
        "placeholder": "BPMN-specific metrics to be implemented",
    }

