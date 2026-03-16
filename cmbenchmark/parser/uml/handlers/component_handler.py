"""Handler for uml:Component elements."""

from typing import Any, Dict
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class ComponentHandler(ElementHandler):
    """Handler for uml:Component elements."""

    @property
    def element_type(self) -> str:
        return "uml:Component"

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        component_id = self.require_xmi_id(ctx, elem, role="Node")
        if not component_id:
            return

        name = self.read_name(elem)
        data: Dict[str, Any] = self.collect_attributes(
            elem,
            scalar_attrs=("visibility",),
            boolean_attrs=("isAbstract", "isLeaf"),
        )

        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        self.upsert_node(
            ctx,
            node_id=component_id,
            node_type="Component",
            name=name,
            data=data,
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
