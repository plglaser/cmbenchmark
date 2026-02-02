"""Type definitions for construct coverage measures."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class ConstructDef:
    """Definition of a construct to match in IR models."""
    id: str  # canonical construct_id (e.g. archimate:BusinessObject, uml:Class)
    kind: str  # "node_type" | "edge_type" | "node_edge_type" | "node_feature" | "edge_feature" | "node_edge_feature"
    match_type: str  # actual type that is used for matching (e.g. BusinessObject, Class)
    match_data_equals: Dict[str, Any] = field(default_factory=dict)  # additional data attributes to match
    meta: Dict[str, Any] = field(default_factory=dict)  # hold additional data, e.g. language-specific like `layer` for ArchiMate nodes

    def matches_node(self, node_type: str, node_data: Dict[str, Any]) -> bool:
        """Check if this construct matches a node."""
        if self.kind not in ("node_type", "node_edge_type", "node_feature", "node_edge_feature"):
            return False
        
        # Check type match
        if self.match_type != node_type:
            return False
        
        # Check data attributes match
        for key, expected_value in self.match_data_equals.items():
            if node_data.get(key) != expected_value:
                return False
        
        return True
    
    def matches_edge(self, edge_type: str, edge_data: Dict[str, Any]) -> bool:
        """Check if this construct matches an edge."""
        if self.kind not in ("edge_type", "node_edge_type", "edge_feature", "node_edge_feature"):
            return False
        
        # Check type match
        if self.match_type != edge_type:
            return False
        
        # Check data attributes match
        for key, expected_value in self.match_data_equals.items():
            if edge_data.get(key) != expected_value:
                return False
        
        return True
