"""Handler for uml:Generalization elements."""

from typing import Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id


class GeneralizationHandler(ElementHandler):
    """Handler for uml:Generalization elements (inheritance relationships)."""

    @property
    def element_type(self) -> str:
        return "uml:Generalization"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "general", "specific"}

    def get_handled_children(self) -> Set[str]:
        return {"general"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Generalization edge."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        gen_id = xmi_id(elem)

        specific_id = elem.attrib.get("specific")
        if not specific_id:
            parent = ctx.parent_map.get(elem)
            if parent is not None:
                specific_id = xmi_id(parent)

        general_id = self.resolve_reference(elem, "general", "general")

        if not specific_id or not general_id:
            gen_label = gen_id or "<no-id>"
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"uml:Generalization edge {gen_label} is missing specific/general "
                f"(specific={specific_id}, general={general_id})",
            )
            return

        edge_id = gen_id or f"{specific_id}__generalization__{general_id}"

        data: dict = {
            "general": general_id,
            "specific": specific_id,
        }
        name = elem.attrib.get("name")
        if name:
            data["name"] = name

        ctx.add_edge(
            Edge(
                id=edge_id,
                sourceId=specific_id,
                targetId=general_id,
                type="Generalization",
                data=data,
            )
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
