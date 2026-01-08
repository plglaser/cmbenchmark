"""Handler for uml:Package elements."""

from typing import Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node, Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id


class PackageHandler(ElementHandler):
    """Handler for uml:Package elements."""

    @property
    def element_type(self) -> str:
        return "uml:Package"

    def get_handled_attributes(self) -> Set[str]:
        return {"name"}

    def get_handled_children(self) -> Set[str]:
        return {"packagedElement", "ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Package node and containment edges."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        pkg_id = xmi_id(elem)
        if not pkg_id:
            return

        pkg_name = elem.attrib.get("name", "")

        # Create package node if not already exists
        if pkg_id not in ctx.nodes_by_id:
            data = {}

            # Extract documentation
            doc = self.extract_documentation(elem)
            if doc:
                data["documentation"] = doc

            ctx.add_node(Node(id=pkg_id, type="Package", name=pkg_name, data=data))

        # Create containment edge from parent package (handled in parser's _create_containment_edges)

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

