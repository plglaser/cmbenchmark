"""Indexer that builds a canonical element index from XML root."""

from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .context import ElementView
from .xml_utils import local, get_xmi_id, get_xsi_type, attr


def build_index(root: ET.Element) -> Dict[str, ElementView]:
    """
    Build a canonical index of all elements with xmi:id.
    
    Returns a dictionary mapping xmi:id to ElementView.
    Metaclasses are canonicalized (e.g., "Class" not "uml:Class").
    Special tags are normalized (ownedUseCase -> UseCase, etc.).
    """
    index: Dict[str, ElementView] = {}
    
    # Track package hierarchy for qualified names
    package_stack: List[Tuple[str, str]] = []  # List of (id, name) tuples
    
    def canonicalize_metaclass(tag_local: str, xsi_type: str) -> str:
        """Canonicalize metaclass name."""
        # If xsi:type exists, strip prefix
        if xsi_type:
            if ":" in xsi_type:
                return xsi_type.split(":", 1)[-1]
            return xsi_type
        
        # If no xsi:type, infer from local tag name
        # Normalize special tags
        if tag_local == "ownedUseCase":
            return "UseCase"
        elif tag_local == "generalization":
            return "Generalization"
        elif tag_local == "include":
            return "Include"
        elif tag_local == "extend":
            return "Extend"
        
        return tag_local
    
    def determine_container_id(
        elem: ET.Element,
        tag_local: str,
        parent_id: Optional[str]
    ) -> Optional[str]:
        """Determine container ID for an element."""
        # For generalizations, prefer specific attribute
        if tag_local == "generalization":
            specific_id = attr(elem, "specific")
            if specific_id:
                return specific_id
        
        return parent_id
    
    def process_element(elem: ET.Element, parent_id: Optional[str] = None):
        """Recursively process all elements."""
        elem_id = get_xmi_id(elem)
        tag_local = local(elem.tag)
        xsi_type = get_xsi_type(elem)
        
        # Canonicalize metaclass
        metaclass = canonicalize_metaclass(tag_local, xsi_type)
        
        # Get name
        name = attr(elem, "name")
        
        # Build qualified name parts
        qualified_parts = [p[1] for p in package_stack if p[1]]
        if name:
            qualified_parts.append(name)
        
        # Determine container ID
        container_id = determine_container_id(elem, tag_local, parent_id)
        
        # Index this element if it has an ID
        if elem_id:
            index[elem_id] = ElementView(
                elem=elem,
                id=elem_id,
                name=name,
                metaclass=metaclass,
                tag_local=tag_local,
                container_id=container_id or parent_id,
                qname_parts=qualified_parts.copy(),
            )
        
        # Update package stack for packages
        if tag_local == "Package" or (xsi_type and "Package" in xsi_type):
            if elem_id:
                package_name = name or ""
                package_stack.append((elem_id, package_name))
                # Process children
                for child in elem:
                    process_element(child, elem_id)
                package_stack.pop()
        else:
            # Process children with current parent
            current_parent = elem_id or parent_id
            for child in elem:
                process_element(child, current_parent)
    
    # Start processing from root
    for child in root:
        process_element(child)
    
    return index

