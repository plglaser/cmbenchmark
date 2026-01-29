"""Cross-language metrics."""

from typing import List, Dict, Any
from cmbenchmark.types.ir import IR
from .size_shape import compute_size_shape_metrics
from .diversity import compute_diversity_metrics

__all__ = ["compute_cross_language_metrics"]


def compute_cross_language_metrics(ir_models: List[IR]) -> Dict[str, Any]:
    """Compute all cross-language metrics."""
    size_shape = compute_size_shape_metrics(ir_models)
    diversity = compute_diversity_metrics(ir_models)
    
    return {
        **size_shape,
        **diversity,
    }
