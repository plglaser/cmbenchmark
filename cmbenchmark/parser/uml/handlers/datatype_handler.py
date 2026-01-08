"""Handler for uml:DataType elements."""

from typing import Any, Dict, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id


class DataTypeHandler(ElementHandler):
    """Handler for uml:DataType elements."""

    @property
    def element_type(self) -> str:
        return "uml:DataType"

    def get_handled_attributes(self) -> Set[str]:
        return {"name"}

    def get_handled_children(self) -> Set[str]:
        return {"ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create DataType node."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        data_type_id = xmi_id(elem)
        if not data_type_id:
            return

        name = elem.attrib.get("name", "")
        data: Dict[str, Any] = {}

        # Documentation
        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        ctx.add_node(Node(id=data_type_id, type="DataType", name=name, data=data))

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

