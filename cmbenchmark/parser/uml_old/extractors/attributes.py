"""Attribute extraction utilities."""

from typing import List, Dict, Any
import xml.etree.ElementTree as ET
from ..context import ParseContext
from ..xml_utils import children, first_child, attr, get_xmi_id, get_xsi_type
from .types import resolve_type_ref


def extract_owned_attributes(
    class_elem: ET.Element,
    ctx: ParseContext
) -> List[Dict[str, Any]]:
    """Extract attributes from a class element."""
    attributes = []
    
    # Find attributes by local tag name
    for attr_elem in children(class_elem, "ownedAttribute"):
        attr_id = get_xmi_id(attr_elem)
        attr_name = attr(attr_elem, "name")
        
        if not attr_id or not attr_name:
            continue
        
        attr_data = {
            "id": attr_id,
            "name": attr_name,
        }
        
        # Check for type attribute directly on ownedAttribute
        type_attr_direct = attr(attr_elem, "type")
        
        # Extract type reference from child type element
        type_elem = first_child(attr_elem, "type")
        
        if type_elem is not None:
            type_attr = attr(type_elem, "type")
            href = attr(type_elem, "href")
            xsi_type = get_xsi_type(type_elem)
            
            if xsi_type == "uml:PrimitiveType" and href:
                # External primitive via href
                type_ref_data = resolve_type_ref(None, href, ctx)
                attr_data.update(type_ref_data)
            elif type_attr:
                # Internal reference via type attribute on type element
                type_ref_data = resolve_type_ref(type_attr, None, ctx)
                attr_data.update(type_ref_data)
        elif type_attr_direct:
            # Internal reference via type attribute directly on ownedAttribute
            type_ref_data = resolve_type_ref(type_attr_direct, None, ctx)
            attr_data.update(type_ref_data)
        
        attributes.append(attr_data)
    
    return attributes

