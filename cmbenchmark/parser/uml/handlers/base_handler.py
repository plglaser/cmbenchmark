"""Base handler class for UML element handlers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    localname,
    is_tool_extension,
    read_multiplicity,
    href_to_type_ref,
    parse_boolean,
)


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
        
        # Get handler map from context (for checking if child has handler)
        handler_map = ctx.handler_map
        
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

    def extract_documentation(self, elem: ET.Element) -> str:
        """Extract documentation from ownedComment elements.
        
        This is a shared method used by multiple handlers to extract
        documentation comments from UML elements.
        
        Args:
            elem: XML element to extract documentation from
            
        Returns:
            Concatenated documentation strings, or empty string if none found
        """
        bodies = []
        for comment in elem.findall("./ownedComment"):
            if is_tool_extension(comment):
                continue
            body = comment.attrib.get("body")
            if body:
                bodies.append(body)
        return "\n".join(bodies) if bodies else ""

    def parse_owned_operations(
        self, ctx, owner_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse ownedOperation elements.
        
        This is a shared method for parsing operations from classes and interfaces.
        
        Args:
            ctx: ParseContext instance
            owner_elem: Element containing ownedOperation children
            
        Returns:
            List of operation dictionaries with id, name, visibility, parameters, etc.
        """
        out: List[Dict[str, Any]] = []
        for op in owner_elem.findall("./ownedOperation"):
            if is_tool_extension(op):
                continue

            op_id = xmi_id(op)
            if not op_id:
                continue

            item: Dict[str, Any] = {"id": op_id}

            op_name = op.attrib.get("name")
            if op_name:
                item["name"] = op_name

            # Visibility
            if "visibility" in op.attrib:
                item["visibility"] = op.attrib["visibility"]

            # Parameters
            params = self.parse_owned_parameters(ctx, op)
            if params:
                item["parameters"] = params

            out.append(item)

        return out

    def parse_owned_parameters(
        self, ctx, owner_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse ownedParameter elements (typically from operations).
        
        Args:
            ctx: ParseContext instance
            owner_elem: Element containing ownedParameter children
            
        Returns:
            List of parameter dictionaries with id, name, type, direction, etc.
        """
        params = []
        for param in owner_elem.findall("./ownedParameter"):
            if is_tool_extension(param):
                continue
            param_id = xmi_id(param)
            if param_id:
                param_data: Dict[str, Any] = {"id": param_id}
                param_name = param.attrib.get("name")
                if param_name:
                    param_data["name"] = param_name
                
                # Direction
                if param.attrib.get("direction") == "return":
                    param_data["direction"] = "return"
                
                # isUnique attribute
                is_unique = parse_boolean(param.attrib.get("isUnique"))
                if is_unique is not None:
                    param_data["isUnique"] = is_unique
                
                # Type resolution (check nested type first, then referenced type)
                type_elem = param.find("./type")
                if type_elem is not None and "href" in type_elem.attrib:
                    # Nested type with href (e.g., PrimitiveType)
                    param_data["type"] = href_to_type_ref(type_elem.attrib["href"])
                else:
                    # Referenced type (via type attribute)
                    type_id = param.attrib.get("type")
                    if type_id:
                        param_data["typeRef"] = type_id
                
                params.append(param_data)
        return params

    def resolve_property_type(self, ctx, prop: ET.Element) -> Optional[str]:
        """Resolve the type reference for a property.
        
        Checks both referenced type (via type attribute) and nested type
        with href (e.g., PrimitiveType).
        
        Args:
            ctx: ParseContext instance
            prop: Property element to resolve type for
            
        Returns:
            Type reference string, or None if not found
        """
        # Check for referenced type
        type_id = prop.attrib.get("type")
        if type_id:
            return type_id

        # Check for nested type with href
        type_elem = prop.find("./type")
        if type_elem is not None and "href" in type_elem.attrib:
            return href_to_type_ref(type_elem.attrib["href"])

        return None

