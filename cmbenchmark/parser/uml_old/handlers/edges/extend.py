"""Handler for Extend edges."""

from typing import Optional
from cmbenchmark.types.ir import Edge
from ...context import ElementView, ParseContext
from ...xml_utils import attr


class ExtendHandler:
    """Handler for Extend metaclass."""
    
    metaclasses = ("Extend",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Edge]:
        """Build an Edge for Extend."""
        extend_id = v.id
        extension = attr(v.elem, "extension")
        extended_case = attr(v.elem, "extendedCase")
        extension_location = attr(v.elem, "extensionLocation")
        
        if not extend_id or not extension or not extended_case:
            return None
        
        edge_data = {
            "extension": extension,
            "extendedCase": extended_case,
        }
        
        if extension_location:
            edge_data["extensionLocation"] = extension_location
        
        return Edge(
            id=extend_id,
            sourceId=extension,
            targetId=extended_case,
            type="Extend",
            data=edge_data
        )

