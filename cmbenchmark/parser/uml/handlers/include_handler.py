"""Handler for include relationships in Use Cases."""

import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id


class IncludeHandler(ElementHandler):
    """Handler for include elements."""

    @property
    def element_type(self) -> str:
        return "uml:Include"

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        include_id = xmi_id(elem)
        source_id = elem.attrib.get("includingCase")
        target_id = self.resolve_reference(elem, "addition", "addition")

        if not source_id or not target_id:
            include_id = xmi_id(elem) or "<no-id>"
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"uml:Include edge {include_id} is missing includingCase/addition "
                f"(includingCase={source_id}, addition={target_id})",
            )
            return

        edge_id = include_id or f"{source_id}__includes__{target_id}"
        ctx.add_edge(
            Edge(
                id=edge_id,
                sourceId=source_id,
                targetId=target_id,
                type="includes",
                data={},
            )
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
