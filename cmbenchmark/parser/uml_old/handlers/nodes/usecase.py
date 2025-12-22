"""Handler for UseCase nodes."""

from typing import Optional
from cmbenchmark.types.ir import Node
from ...context import ElementView, ParseContext
from ...extractors.documentation import extract_documentation
from ...extractors.qualified_name import build_qualified_name
from ...xml_utils import children, get_xmi_id, attr


class UseCaseHandler:
    """Handler for UseCase metaclass."""
    
    metaclasses = ("UseCase",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Node]:
        """Build a Node for UseCase."""
        if not v.id or not v.name:
            return None
        
        # Build qualified name from container chain
        qualified_name = build_qualified_name(v, ctx)
        
        # Extract extension points
        extension_points = []
        for ext_point in children(v.elem, "extensionPoint"):
            ext_point_id = get_xmi_id(ext_point)
            ext_point_name = attr(ext_point, "name")
            use_case_ref = attr(ext_point, "useCase")
            if ext_point_id and ext_point_name:
                extension_points.append({
                    "id": ext_point_id,
                    "name": ext_point_name,
                    "useCase": use_case_ref,
                })
        
        node_data = {
            "qualifiedName": qualified_name,
            "extensionPoints": extension_points,
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

