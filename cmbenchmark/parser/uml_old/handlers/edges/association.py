"""Handler for Association edges."""

from typing import Optional
from cmbenchmark.types.ir import Edge
from ...context import ElementView, ParseContext
from ...xml_utils import children, first_child, attr, get_xmi_id
from ...extractors.multiplicity import get_multiplicity


class AssociationHandler:
    """Handler for Association metaclass."""
    
    metaclasses = ("Association",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Edge]:
        """Build an Edge for Association."""
        if not v.id:
            return None
        
        # Get owned ends
        owned_ends = children(v.elem, "ownedEnd")
        if len(owned_ends) != 2:
            return None
        
        end1 = owned_ends[0]
        end2 = owned_ends[1]
        
        # Extract end information
        end1_id = get_xmi_id(end1)
        end1_type = attr(end1, "type")
        end1_role = attr(end1, "name")
        end1_agg = attr(end1, "aggregation", "none")
        
        end2_id = get_xmi_id(end2)
        end2_type = attr(end2, "type")
        end2_role = attr(end2, "name")
        end2_agg = attr(end2, "aggregation", "none")
        
        if not end1_type or not end2_type:
            return None
        
        # Extract multiplicities
        end1_lower_elem = first_child(end1, "lowerValue")
        end1_upper_elem = first_child(end1, "upperValue")
        end2_lower_elem = first_child(end2, "lowerValue")
        end2_upper_elem = first_child(end2, "upperValue")
        
        end1_lower = get_multiplicity(end1_lower_elem)
        end1_upper = get_multiplicity(end1_upper_elem)
        end2_lower = get_multiplicity(end2_lower_elem)
        end2_upper = get_multiplicity(end2_upper_elem)
        
        # Build end data
        end1_data = {
            "id": end1_id or "",
            "role": end1_role,
            "lower": int(end1_lower) if end1_lower and end1_lower.isdigit() else None,
            "upper": end1_upper if end1_upper else None,
            "aggregation": end1_agg,
        }
        
        end2_data = {
            "id": end2_id or "",
            "role": end2_role,
            "lower": int(end2_lower) if end2_lower and end2_lower.isdigit() else None,
            "upper": end2_upper if end2_upper else None,
            "aggregation": end2_agg,
        }
        
        # Determine edge type based on aggregation
        edge_type = "Composition" if (end1_agg == "composite" or end2_agg == "composite") else "Association"
        
        # Create edge data
        edge_data = {
            "name": v.name,
            "end1": end1_data,
            "end2": end2_data,
        }
        
        return Edge(
            id=v.id,
            sourceId=end1_type,
            targetId=end2_type,
            type=edge_type,
            data=edge_data
        )

