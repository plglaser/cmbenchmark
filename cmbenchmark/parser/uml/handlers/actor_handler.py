"""Handler for uml:Actor elements."""

from typing import Any, Dict, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    localname,
)


class ActorHandler(ElementHandler):
    """Handler for uml:Actor elements."""

    @property
    def element_type(self) -> str:
        return "uml:Actor"

    def get_handled_attributes(self) -> Set[str]:
        return {"name"}

    def get_handled_children(self) -> Set[str]:
        return set()

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Actor node."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        actor_id = xmi_id(elem)
        if not actor_id:
            return

        name = elem.attrib.get("name", "")
        data: Dict[str, Any] = {}

        ctx.add_node(Node(id=actor_id, type="Actor", name=name, data=data))

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

