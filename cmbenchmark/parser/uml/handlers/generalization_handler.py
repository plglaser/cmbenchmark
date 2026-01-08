"""Handler for uml:Generalization elements."""

from typing import Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id
)


class GeneralizationHandler(ElementHandler):
    """Handler for uml:Generalization elements (inheritance relationships)."""

    @property
    def element_type(self) -> str:
        return "uml:Generalization"

    def get_handled_attributes(self) -> Set[str]:
        return {"general", "specific", "name"}

    def get_handled_children(self) -> Set[str]:
        return set()  # Generalizations typically don't have handled children

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Generalization edge."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        gen_id = xmi_id(elem)
        if not gen_id:
            return

        specific_id = elem.attrib.get("specific")
        general_id = elem.attrib.get("general")

        if not specific_id or not general_id:
            return

        data: dict = {}
        name = elem.attrib.get("name")
        if name:
            data["name"] = name
        data["general"] = general_id
        data["specific"] = specific_id

        ctx.add_edge(
            Edge(
                id=gen_id,
                sourceId=specific_id,
                targetId=general_id,
                type="Generalization",
                data=data,
            )
        )

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

