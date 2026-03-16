"""Handler for uml:Actor elements."""

from typing import Any, Dict
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class ActorHandler(ElementHandler):
    """Handler for uml:Actor elements."""

    @property
    def element_type(self) -> str:
        return "uml:Actor"

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Actor node."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        actor_id = self.require_xmi_id(ctx, elem, role="Node")
        if not actor_id:
            return

        name = self.read_name(elem)
        data: Dict[str, Any] = self.collect_attributes(
            elem,
            scalar_attrs=("visibility", "href"),
            boolean_attrs=("isAbstract", "isLeaf"),
        )
        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        self.upsert_node(
            ctx,
            node_id=actor_id,
            node_type="Actor",
            name=name,
            data=data,
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
