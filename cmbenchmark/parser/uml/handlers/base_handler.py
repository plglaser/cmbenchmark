"""Base handler class for UML element handlers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.xmi_utils import xmi_id, xsi_type, localname


class ElementHandler(ABC):
    """Base class for element-specific handlers.
    
    Each handler is responsible for parsing a specific UML element type
    (e.g., uml:Class, uml:Package, uml:Association).
    """

    @property
    @abstractmethod
    def element_type(self) -> str:
        """Return the xsi:type this handler processes (e.g., 'uml:Class')."""
        pass

    @abstractmethod
    def handle(self, ctx, elem: ET.Element) -> None:
        """Handle a single element of this handler's type.
        
        Args:
            ctx: ParseContext instance
            elem: XML element to process
        """
        pass

    def get_handled_attributes(self) -> Set[str]:
        """Return set of attribute names this handler processes.
        
        Override to specify which attributes are handled. Attributes not in this
        set will be logged as unhandled.
        
        Returns:
            Set of attribute names (e.g., {'name', 'isAbstract', 'visibility'})
        """
        return set()

    def get_handled_children(self) -> Set[str]:
        """Return set of child element tags this handler processes.
        
        Override to specify which child elements are handled. Child elements not
        in this set will be logged as unhandled.
        
        Returns:
            Set of child tag names (e.g., {'ownedAttribute', 'ownedOperation'})
        """
        return set()

    def log_unhandled_attributes(
        self, ctx, elem: ET.Element, handled: Set[str]
    ) -> None:
        """Log unhandled attributes for an element."""
        elem_id = xmi_id(elem)
        elem_type = xsi_type(elem) or localname(elem.tag)
        
        for attr_name, attr_value in elem.attrib.items():
            # Skip XMI/XSI namespace attributes (they're in {namespace}format)
            if attr_name.startswith("{"):
                continue
            
            # Get local name for comparison (handlers declare local names)
            attr_local = localname(attr_name) if "}" in attr_name else attr_name
            
            # Skip standard XMI/XSI attributes
            if attr_local in {"id", "type"}:
                continue
            
            # Check if attribute is handled (compare local name)
            if attr_local not in handled:
                print(f"[UNHANDLED ATTRIBUTE] Element: {elem_type} (ID: {elem_id}), Attribute: {attr_local}, Value: {attr_value}")

    def log_unhandled_children(
        self, ctx, elem: ET.Element, handled: Set[str]
    ) -> None:
        """Log unhandled child elements."""
        elem_id = xmi_id(elem)
        elem_type = xsi_type(elem) or localname(elem.tag)
        
        # Get handler map from context if available (for checking if child has handler)
        handler_map = getattr(ctx, '_handler_map', None)
        
        for child in elem:
            child_tag = localname(child.tag)
            # Skip tool extensions
            if child_tag in {"Extension", "eAnnotations", "details"}:
                continue
            
            # Special handling for packagedElement - check if the actual element type has a handler
            if child_tag == "packagedElement":
                child_type = xsi_type(child)
                if handler_map and child_type and child_type in handler_map:
                    # This packagedElement is handled by its xsi:type handler
                    continue
            
            if child_tag not in handled:
                child_id = xmi_id(child)
                child_type = xsi_type(child)
                if child_type:
                    print(f"[UNHANDLED CHILD] Element: {elem_type} (ID: {elem_id}), Child: {child_tag} (xsi:type={child_type}, ID: {child_id})")
                else:
                    print(f"[UNHANDLED CHILD] Element: {elem_type} (ID: {elem_id}), Child: {child_tag} (ID: {child_id})")

