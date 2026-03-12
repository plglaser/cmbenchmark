"""Handler for uml:Enumeration elements."""

from typing import Any, Dict, List, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id, is_tool_extension


class EnumerationHandler(ElementHandler):
    """Handler for uml:Enumeration elements."""

    @property
    def element_type(self) -> str:
        return "uml:Enumeration"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "visibility", "href"}

    def get_handled_children(self) -> Set[str]:
        return {"ownedLiteral", "ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Enumeration node with literals."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        enum_id = self.require_xmi_id(ctx, elem, role="Node")
        if not enum_id:
            return

        name = self.read_name(elem)
        data: Dict[str, Any] = self.collect_attributes(elem, scalar_attrs=("visibility", "href"))

        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        literals = self._parse_literals(ctx, elem)
        if literals:
            data["literals"] = literals

        ctx.add_node(Node(id=enum_id, type="Enumeration", name=name, data=data))

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _parse_literals(self, ctx, elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse ownedLiteral elements."""
        literals = []
        for lit in elem.findall("./ownedLiteral"):
            if is_tool_extension(lit):
                continue

            lit_id = self.require_xmi_id(ctx, lit, role="Enumeration literal")
            if not lit_id:
                continue

            lit_data: Dict[str, Any] = {"id": lit_id}

            lit_name = self.read_name(lit)
            if lit_name:
                lit_data["name"] = lit_name

            literals.append(lit_data)

        return literals
