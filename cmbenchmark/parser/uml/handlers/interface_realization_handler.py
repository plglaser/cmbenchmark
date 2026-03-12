"""Handler for interfaceRealization elements."""

from typing import Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xmi_id


class InterfaceRealizationHandler(ElementHandler):
    """Handler for interface realization relationships."""

    @property
    def element_type(self) -> str:
        return "uml:InterfaceRealization"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "client", "supplier", "implementingClassifier", "contract"}

    def get_handled_children(self) -> Set[str]:
        return {"supplier", "contract"}

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        rel_id = xmi_id(elem)

        source_id = elem.attrib.get("implementingClassifier") or elem.attrib.get("client")
        target_id = self.resolve_reference(elem, "contract", "contract") or elem.attrib.get("supplier")

        if not source_id or not target_id:
            rel_label = rel_id or "<no-id>"
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"uml:InterfaceRealization edge {rel_label} is missing source/target "
                f"(source={source_id}, target={target_id})",
            )
            return

        edge_id = rel_id or f"{source_id}__realizes__{target_id}"
        data = {
            "client": elem.attrib.get("client"),
            "supplier": elem.attrib.get("supplier"),
            "implementingClassifier": elem.attrib.get("implementingClassifier"),
            "contract": elem.attrib.get("contract"),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if "name" in elem.attrib:
            data["name"] = elem.attrib["name"]

        ctx.add_edge(
            Edge(
                id=edge_id,
                sourceId=source_id,
                targetId=target_id,
                type="InterfaceRealization",
                data=data,
            )
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
