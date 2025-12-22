"""Type resolution utilities."""

from typing import Dict, Any, Optional
from ..context import ParseContext


def resolve_type_ref(
    type_attr: Optional[str],
    href: Optional[str],
    ctx: ParseContext
) -> Dict[str, Any]:
    """
    Resolve type reference from either type attribute or href.
    
    Returns dict with typeRef and optionally typeRefName.
    """
    result: Dict[str, Any] = {}
    
    if href:
        # External primitive via href (e.g., PrimitiveTypes::String)
        # Extract the type name from href
        if "#//" in href:
            type_name = href.split("#//")[-1]
            # Map common namespaces
            if "PrimitiveTypes" in href:
                result["typeRef"] = f"PrimitiveTypes::{type_name}"
            elif "GenMyModelPrimitiveTypes" in href:
                result["typeRef"] = f"GenMyModel::{type_name}"
            else:
                result["typeRef"] = type_name
        else:
            result["typeRef"] = href
    elif type_attr:
        # Internal reference via type attribute
        result["typeRef"] = type_attr
        # Try to resolve name if we've seen this ID
        if type_attr in ctx.id_to_name:
            result["typeRefName"] = ctx.id_to_name[type_attr]
    
    return result

