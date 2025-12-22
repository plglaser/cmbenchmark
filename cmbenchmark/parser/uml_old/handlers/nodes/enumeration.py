"""Handler for Enumeration nodes."""

from typing import Optional
from cmbenchmark.types.ir import Node
from ...context import ElementView, ParseContext
from ...extractors.documentation import extract_documentation
from ...extractors.qualified_name import build_qualified_name
from ...xml_utils import children, get_xmi_id, attr


class EnumerationHandler:
    """Handler for Enumeration metaclass."""
    
    metaclasses = ("Enumeration",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Node]:
        """Build a Node for Enumeration."""
        if not v.id or not v.name:
            return None
        
        # Build qualified name from container chain
        qualified_name = build_qualified_name(v, ctx)
        
        # Extract literals
        literals = []
        for literal in children(v.elem, "ownedLiteral"):
            literal_id = get_xmi_id(literal)
            literal_name = attr(literal, "name")
            if literal_id and literal_name:
                literals.append({
                    "id": literal_id,
                    "name": literal_name,
                })
        
        node_data = {
            "qualifiedName": qualified_name,
            "literals": literals,
        }
        
        # Extract documentation
        documentation = extract_documentation(v.elem)
        if documentation:
            node_data["documentation"] = documentation
        
        return Node(
            id=v.id,
            type=v.metaclass,
            name=v.name,
            data=node_data
        )

