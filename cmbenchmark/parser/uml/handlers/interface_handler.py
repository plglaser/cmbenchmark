"""Handler for uml:Interface elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id
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

        # Documentation
        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        # Operations
        ops = self.parse_owned_operations(ctx, elem)
        if ops:
            data["operations"] = ops

        ctx.add_node(Node(id=interface_id, type="Interface", name=name, data=data))

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

