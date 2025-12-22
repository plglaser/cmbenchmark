"""Handler for Class, Component, and Actor nodes."""

from typing import Optional
from cmbenchmark.types.ir import Node
from ...context import ElementView, ParseContext
from ...extractors.attributes import extract_owned_attributes
from ...extractors.documentation import extract_documentation
from ...extractors.qualified_name import build_qualified_name


class ClasslikeHandler:
    """Handler for Class, Component, and Actor metaclasses."""
    
    metaclasses = ("Class", "Component", "Actor")
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Node]:
        """Build a Node for Class, Component, or Actor."""
        if not v.id or not v.name:
            return None
        
        # Extract attributes
        attributes = extract_owned_attributes(v.elem, ctx)
        
        # Build qualified name from container chain
        qualified_name = build_qualified_name(v, ctx)
        
        node_data = {
            "qualifiedName": qualified_name,
            "attributes": attributes,
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

