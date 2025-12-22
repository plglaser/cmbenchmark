"""Handler for Generalization edges."""

from typing import Optional
from cmbenchmark.types.ir import Edge
from ...context import ElementView, ParseContext
from ...xml_utils import attr


class GeneralizationHandler:
    """Handler for Generalization metaclass."""
    
    metaclasses = ("Generalization",)
    
    def build(self, v: ElementView, ctx: ParseContext) -> Optional[Edge]:
        """Build an Edge for Generalization."""
        gen_id = v.id
        general_id = attr(v.elem, "general")
        specific_id = attr(v.elem, "specific")
        
        # If specific is not set, try to use container_id
        if not specific_id:
            if v.container_id:
                specific_id = v.container_id
        
        if not gen_id or not general_id or not specific_id:
            return None
        
        return Edge(
            id=gen_id,
            sourceId=specific_id,
            targetId=general_id,
            type="Generalization",
            data={}
        )

