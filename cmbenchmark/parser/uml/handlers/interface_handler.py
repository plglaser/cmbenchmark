"""Handler for uml:Interface elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    read_multiplicity,
    href_to_type_ref,
    parse_boolean,
    localname,
)


class InterfaceHandler(ElementHandler):
    """Handler for uml:Interface elements."""

    @property
    def element_type(self) -> str:
        return "uml:Interface"

    def get_handled_attributes(self) -> Set[str]:
        return {"name"}

    def get_handled_children(self) -> Set[str]:
        return {"ownedOperation", "generalization", "ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Interface node with operations."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        interface_id = xmi_id(elem)
        if not interface_id:
            return

        name = elem.attrib.get("name", "")
        data: Dict[str, Any] = {}

        # Qualified name
        qn = ctx.qname(interface_id)
        if qn:
            data["qualifiedName"] = qn

        # Documentation
        doc = self._extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        # Operations
        ops = self._parse_owned_operations(ctx, elem)
        if ops:
            data["operations"] = ops

        ctx.add_node(Node(id=interface_id, type="Interface", name=name, data=data))

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _extract_documentation(self, elem: ET.Element) -> str:
        """Extract documentation from ownedComment elements."""
        bodies = []
        for comment in elem.findall("./ownedComment"):
            if is_tool_extension(comment):
                continue
            body = comment.attrib.get("body")
            if body:
                bodies.append(body)
        return "\n".join(bodies) if bodies else ""

    def _parse_owned_operations(
        self, ctx, interface_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse ownedOperation elements."""
        out: List[Dict[str, Any]] = []
        for op in interface_elem.findall("./ownedOperation"):
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
            params = []
            for param in op.findall("./ownedParameter"):
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
                            # Try to resolve qualified name, fallback to ID
                            type_qname = ctx.qname(type_id)
                            if type_qname:
                                param_data["type"] = type_qname
                            param_data["typeRef"] = type_id
                    
                    params.append(param_data)
            if params:
                item["parameters"] = params

            out.append(item)

        return out

