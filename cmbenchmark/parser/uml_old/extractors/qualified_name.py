"""Qualified name extraction utilities."""

from typing import List, Optional
from ..context import ElementView, ParseContext


STOP_METACLASSES = {"Model"}  # Stop at Model, optionally also stop at Package if desired


def build_qualified_name(v: ElementView, ctx: ParseContext) -> str:
    """
    Build qualified name by walking the container_id chain.
    
    Args:
        v: ElementView to build qualified name for
        ctx: ParseContext containing the index
        
    Returns:
        Qualified name as a string (e.g., "Library Management::Maintain book in records")
    """
    parts: List[str] = []
    cur: Optional[ElementView] = v
    
    while cur:
        if cur.name:
            parts.append(cur.name)
        
        if not cur.container_id:
            break
        
        parent = ctx.index.get(cur.container_id)
        if not parent:
            break
        
        if parent.metaclass in STOP_METACLASSES:
            # Stop at Model (don't include Model name in qualified name)
            # If you want Model name included, uncomment the line below
            # parts.append(parent.name)
            break
        
        cur = parent
    
    return "::".join(reversed(parts))

