"""Handler for Include edges."""

from typing import Optional
from cmbenchmark.types.ir import Edge
from ...context import ElementView, ParseContext
from ...xml_utils import attr


class IncludeHandler:
    """Handler for Include metaclass."""
    
    metaclasses = ("Include",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Edge]:
        """Build an Edge for Include."""
        include_id = v.id
        including_case = attr(v.elem, "includingCase")
        addition = attr(v.elem, "addition")
        
        if not include_id or not including_case or not addition:
            return None
        
        edge_data = {
            "includingCase": including_case,
            "addition": addition,
        }
        
        return Edge(
            id=include_id,
            sourceId=including_case,
            targetId=addition,
            type="Include",
            data=edge_data
        )

