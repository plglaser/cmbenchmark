"""ArchiMate-specific validation for IR models."""

from typing import List
from cmbenchmark.types.ir import IR
from cmbenchmark.parser.archimate.archimate_types import (
    ALL_ELEMENT_TYPES,
    ALL_RELATIONSHIP_TYPES,
)


def validate_archimate(ir: IR) -> List[str]:
    """
    Validate an ArchiMate IR structure against known ArchiMate types.

    Args:
        ir: The IR object to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate node types
    for node in ir.nodes:
        node_type = node.type
        if not node_type:
            errors.append(f"Node {node.id} missing type")
        elif node_type not in ALL_ELEMENT_TYPES:
            errors.append(f"Node {node.id} has unknown element type: {node_type}")
    
    # Validate edge types
    for edge in ir.edges:
        edge_type = edge.type
        if not edge_type:
            errors.append(f"Edge {edge.id} missing type")
        elif edge_type not in ALL_RELATIONSHIP_TYPES:
            errors.append(f"Edge {edge.id} has unknown relationship type: {edge_type}")
    
    return errors

